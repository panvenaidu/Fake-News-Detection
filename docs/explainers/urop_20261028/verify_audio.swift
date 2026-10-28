import Foundation
import AVFoundation
import AudioToolbox
let asset=AVURLAsset(url:URL(fileURLWithPath:CommandLine.arguments[1]));guard let track=asset.tracks(withMediaType:.audio).first else {fatalError("No audio")}
let reader=try AVAssetReader(asset:asset)
let out=AVAssetReaderTrackOutput(track:track,outputSettings:[AVFormatIDKey:kAudioFormatLinearPCM,AVLinearPCMIsFloatKey:true,AVLinearPCMBitDepthKey:32,AVLinearPCMIsNonInterleaved:false]);reader.add(out);guard reader.startReading() else {fatalError("Cannot decode audio")}
var n:Int64=0;var energy:Double=0;var peak:Float=0;var nonfinite=0
while let sample=out.copyNextSampleBuffer(){
 guard let buffer=CMSampleBufferGetDataBuffer(sample) else {continue}
 let size=CMBlockBufferGetDataLength(buffer);var bytes=[UInt8](repeating:0,count:size)
 CMBlockBufferCopyDataBytes(buffer,atOffset:0,dataLength:size,destination:&bytes)
 bytes.withUnsafeBytes { raw in
  for v in raw.bindMemory(to:Float.self) {if !v.isFinite {nonfinite += 1};energy += Double(v)*Double(v);peak=max(peak,abs(v));n += 1}
 }
}
guard reader.status == .completed else {fatalError("Audio decode failure")}
let rms=sqrt(energy/Double(max(1,n)));guard n>0 && rms>0.005 && peak>0.05 && nonfinite==0 else {fatalError("Silent or invalid audio")}
let o:[String:Any]=["status":"passed_full_encoded_audio_decode","samples":n,"rms":rms,"peak":peak,"nonfinite":nonfinite,"duration":CMTimeGetSeconds(asset.duration)]
print(String(data:try JSONSerialization.data(withJSONObject:o,options:.sortedKeys),encoding:.utf8)!)
