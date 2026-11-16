"""Prospective quota allocation and deterministic validation-only selection."""
import math

from vit83 import DINO, RECIPES, READ, RESERVE_SECONDS, BASELINE_VALIDATION_CORRECT, recipe_cfg
from train_vit_finetune_v1 import barrier, rank, require, save_json, selection, sha, stamp, train_trial


def register(out, buffer, cfg, session, base):
    path = out/'registration.json'
    env = session['environment']
    preflight = READ(out/'sessions.json')[0]
    pin = {k: preflight['environment'][k] for k in ('python', 'packages', 'cuda', 'cudnn', 'optional_packages')}
    require(all(env[k] == v for k,v in pin.items()), 'GPU environment differs from saved preflight')
    require(session['world_size'] == preflight['world_size'] == 2, 'GPU topology differs')
    require(env['free_bytes_working'] >= 13 * 1024**3, 'Insufficient space for recovery checkpoints')
    if path.exists():
        registered = READ(path)
        require(registered['config'] == cfg and registered['cohort_sha256'] == sha(out/'cohort_contract.json'),
                'Registered recipe/cohort changed')
        return registered
    require(preflight['state'] == 'preflight_complete', 'Reopen a completed preflight before registration')
    refs = {}
    costs = {}
    for recipe in RECIPES:
        receipt = out/'engineering'/recipe/'preflight/timing.json'
        if recipe == 'dinov2' and (out/'dinov2_unavailable.json').exists():
            continue
        timing = READ(receipt)
        require(timing['continuation_passed'] and timing['validation_reload_exact']
                and timing['encoder_and_head_changed'] and timing['effective_batch'] == 64
                and timing['device_count_used'] == 2, f'Engineering gates failed for {recipe}')
        refs[recipe] = sha(receipt)

        def epoch_cost(rows):
            train = rows / timing['train_rows_per_second']
            validation = 59299 / timing['validation_rows_per_second']
            ckpt = timing['checkpoint_seconds'] * (math.ceil(train / 350) + 2)
            return 1.11 * (train + validation + ckpt + 15)

        costs[recipe] = {'pilot_seconds': 2 * epoch_cost(30000), 'epoch_seconds': epoch_cost(563601)}

    # Keep six GPU hours disjoint from exploration and include saved-output turnaround.
    # Resolution is optional and omitted from this quota allocation before any other reductions.
    remaining = 30 * 3600 - math.ceil(session['quota_used_minutes_observed']) * 60
    usable = min(remaining - RESERVE_SECONDS, session['duration_cap_seconds']) - max(0, session['setup_seconds']) - 600
    recipes = [r for r in RECIPES if r in refs]
    choices = []
    for trial_count, trial_recipes in [(2, recipes), (1, recipes),
                                       (1, [r for r in recipes if r != 'dinov2']),
                                       (1, list(RECIPES[:2]))]:
        alternatives = [r for r in trial_recipes if r != 'crop']
        if len(alternatives) < trial_count:
            continue
        pilot = sum(costs[r]['pilot_seconds'] for r in trial_recipes)
        worst = sum(sorted((costs[r]['epoch_seconds'] for r in alternatives), reverse=True)[:trial_count])
        for cap in (6, 4):
            if pilot + cap * worst <= usable:
                choices.append((trial_count, trial_recipes, cap, pilot + cap * worst))
                break
    require(choices, 'Free quota cannot fit both framing pilots and a four-epoch full trial with reserve')
    count, recipes, cap, estimated = choices[0]
    pilots = [{'id': f'pilot_{r}', 'recipe': r, 'kind': 'pilot', 'epochs': 2,
               'rows': 30000, 'lr': 3e-5, 'variant': DINO if r == 'dinov2' else base} for r in recipes]
    record = {'utc': stamp(), 'config': cfg, 'cohort_sha256': sha(out/'cohort_contract.json'),
              'engineering_sha256': refs, 'world_size': 2, 'environment_pin': pin, 'pilots': pilots,
              'budget': {'free_gpu_hours_observed': remaining / 3600, 'protected_gpu_hours': 6,
                         'planning_window_seconds': usable, 'estimate_seconds': estimated,
                         'per_recipe': costs, 'full_trial_cap': count, 'epoch_cap': cap,
                         'omitted_pilots': [r for r in RECIPES if r not in recipes],
                         'resolution_extension': 'omitted to protect full-trial and test capacity'}}
    save_json(path, record)
    print('budget_registered', record['budget'], flush=True)
    return record


def train(buffer, out, cfg, store, frames, device):
    path = out/'registration.json'
    reg = READ(path)
    deadline = READ(buffer/'session.json')['deadline_epoch']

    def run(trial):
        return train_trial(frames, store, recipe_cfg(cfg, trial['recipe']), device,
                           trial, out/trial['id'], sha(path), deadline)

    pilots = []
    for trial in reg['pilots']:
        result = run(trial)
        if result is None:
            return
        pilots.append(result)
    ranked = sorted(pilots, key=lambda r: selection(r['best']), reverse=True)
    alternatives = [r for r in ranked if r['trial']['recipe'] != 'crop']
    promotes = alternatives[:1]
    if reg['budget']['full_trial_cap'] == 2 and len(alternatives) >= 2:
        # With 59,299 rows, the allowed integer difference is at most 148 correct.
        top, second = (round(r['best']['validation']['accuracy'] * 59299) for r in alternatives[:2])
        if 400 * (top - second) <= 59299:
            promotes.append(alternatives[1])
    full = [{**r['trial'], 'id': f"full_{r['trial']['recipe']}", 'kind': 'full',
             'epochs': reg['budget']['epoch_cap'], 'rows': 563601} for r in promotes]
    promotion = {'full_trials': full, 'pilot_ranking': [{'trial': r['trial']['id'], 'best': r['best']}
                                                       for r in ranked]}
    promote_path = out/'promotion.json'
    if rank() == 0:
        if promote_path.exists():
            require(READ(promote_path) == promotion, 'Saved promotion has changed')
        else:
            save_json(promote_path, promotion)
        print('promoted', [t['id'] for t in full], flush=True)
    barrier()
    finals = []
    for trial in full:
        result = run(trial)
        if result is None:
            return
        finals.append(result)
    trial_order = {recipe: i for i, recipe in enumerate(RECIPES)}
    winner = max(finals, key=lambda r: (*selection(r['best']), -trial_order[r['trial']['recipe']]))
    chosen, best = winner['trial'], winner['best']
    correct = round(best['validation']['accuracy'] * 59299)
    if rank() == 0:
        receipt = {'registration_sha256': sha(path), 'promotion_sha256': sha(promote_path),
                   'final_trial': chosen, 'selected': best, 'validation_correct': correct,
                   'prior_validation_correct': BASELINE_VALIDATION_CORRECT,
                   'finalists': {r['trial']['id']: {'trial': r['trial'], 'selected': r['best'],
                                 'complete_sha256': sha(out/r['trial']['id']/'complete.json')} for r in finals},
                   'complete_sha256': sha(out/chosen['id']/'complete.json'),
                   'seed': cfg['seed'], 'additional_seeds': []}
        require(sha(out/chosen['id']/best['selected_weight']) == best['weight_sha256'],
                'Selected checkpoint differs')
        if correct > BASELINE_VALIDATION_CORRECT:
            filename, state = 'selection_frozen.json', 'frozen_before_test'
        else:
            filename, state = 'baseline_retained.json', 'baseline_retained'
        if (out/filename).exists():
            require({k: v for k, v in READ(out/filename).items() if k != 'utc'} == {**receipt, 'state': state},
                    'Existing final selection differs')
        else:
            save_json(out/filename, {**receipt, 'state': state, 'utc': stamp()})
        print(state, chosen['id'], best, flush=True)
    barrier()
