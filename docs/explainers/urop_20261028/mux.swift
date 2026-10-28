import Foundation
import AVFoundation
let args=CommandLine.arguments
if args.count==3 && args[1]=="inspect" {
 let a=AVURLAsset(url:URL(fileURLWithPath:args[2]))
 let v=a.tracks(withMediaType:.video); let s=a.tracks(withMediaType:.audio)
 let obj:[String:Any]=["duration":CMTimeGetSeconds(a.duration),"videoTracks":v.count,"audioTracks":s.count,"width":v.first?.naturalSize.width ?? 0,"height":v.first?.naturalSize.height ?? 0,"fps":v.first?.nominalFrameRate ?? 0]
 print(String(data:try! JSONSerialization.data(withJSONObject:obj,options:.sortedKeys),encoding:.utf8)!)
 exit(v.count==1 && s.count==1 ? 0:1)
}
guard args.count==4 else { fatalError("usage: mux video audio output; or inspect output") }
let va=AVURLAsset(url:URL(fileURLWithPath:args[1]));let aa=AVURLAsset(url:URL(fileURLWithPath:args[2]));let c=AVMutableComposition()
guard let vt=va.tracks(withMediaType:.video).first,let at=aa.tracks(withMediaType:.audio).first else {fatalError("Missing source track")}
let vd=va.duration;let ad=aa.duration
let cv=c.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid)!
let ca=c.addMutableTrack(withMediaType:.audio,preferredTrackID:kCMPersistentTrackID_Invalid)!
try cv.insertTimeRange(CMTimeRange(start:.zero,duration:vd),of:vt,at:.zero)
try ca.insertTimeRange(CMTimeRange(start:.zero,duration:CMTimeMinimum(vd,ad)),of:at,at:.zero)
guard let e=AVAssetExportSession(asset:c,presetName:AVAssetExportPreset1920x1080) else {fatalError("No export session")}
e.outputURL=URL(fileURLWithPath:args[3]);e.outputFileType = .mp4;e.shouldOptimizeForNetworkUse=true
let semaphore=DispatchSemaphore(value:0)
e.exportAsynchronously { semaphore.signal() }
semaphore.wait()
guard e.status == .completed else {fatalError("Export failed: \(String(describing:e.error))")}
print("Completed narrated MP4 export")
