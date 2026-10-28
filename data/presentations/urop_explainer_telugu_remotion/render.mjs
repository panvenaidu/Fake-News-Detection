import {bundle} from '@remotion/bundler';
import {openBrowser,selectComposition,renderMedia,renderStill} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
const cwd=process.cwd();const timeline=JSON.parse(fs.readFileSync('src/timeline.json','utf8'));
const serveUrl=await bundle({entryPoint:path.join(cwd,'src/index.ts')});
const browser=await openBrowser('chrome',{browserExecutable:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',chromeMode:'chrome-for-testing',chromiumOptions:{headless:true}});
try {
 const composition=await selectComposition({serveUrl,id:'UROPTelugu',puppeteerInstance:browser});
 console.log('Composition',JSON.stringify(composition));
 fs.writeFileSync('evidence/composition.json',JSON.stringify(composition,null,2));
 const frames=timeline.scenes.map((s,i)=>Math.round((s.start+Math.min(8,s.audioDuration*.5))*30));
 const onBrowserLog=(log)=>{if(log.text?.startsWith('UROP_LAYOUT_REPORT '))fs.writeFileSync('evidence/text-layout.json',log.text.slice('UROP_LAYOUT_REPORT '.length));};
 for(let i=0;i<frames.length;i++){await renderStill({serveUrl,composition,puppeteerInstance:browser,frame:frames[i],output:path.join(cwd,`rendered/review_${i}.png`),imageFormat:'png',onBrowserLog});console.log('Review frame',i);}
 if(process.env.STILLS_ONLY==='1')process.exitCode=0;
 else {let last=-1;await renderMedia({serveUrl,composition,puppeteerInstance:browser,codec:'h264',outputLocation:path.join(cwd,'UROP_Telugu_English_Bella.mp4'),crf:19,pixelFormat:'yuv420p',concurrency:3,overwrite:false,onBrowserLog,onProgress:p=>{const n=Math.floor(p.progress*20);if(n!==last){console.log('Render progress',Math.round(p.progress*100));last=n;}}});console.log('Render complete');}
} finally {await browser.close({silent:true});}
