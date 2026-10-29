// Offline pitch-preserving narration tempo; no network or model inference.
import Foundation
import AVFoundation
let a=CommandLine.arguments
guard a.count==4,let rate=Float(a[3]),rate>=1,rate<=1.5 else {fatalError("tempo input.wav output.wav rate")}
let input=try AVAudioFile(forReading:URL(fileURLWithPath:a[1]))
let format=input.processingFormat
let engine=AVAudioEngine();let player=AVAudioPlayerNode();let pitch=AVAudioUnitTimePitch()
pitch.rate=rate;pitch.pitch=0;pitch.overlap=8
engine.attach(player);engine.attach(pitch)
engine.connect(player,to:pitch,format:format)
engine.connect(pitch,to:engine.mainMixerNode,format:format)
try engine.enableManualRenderingMode(.offline,format:format,maximumFrameCount:4096)
let settings:[String:Any]=[AVFormatIDKey:kAudioFormatLinearPCM,AVSampleRateKey:format.sampleRate,AVNumberOfChannelsKey:format.channelCount,AVLinearPCMBitDepthKey:16,AVLinearPCMIsFloatKey:false,AVLinearPCMIsBigEndianKey:false]
var output:AVAudioFile?=try AVAudioFile(forWriting:URL(fileURLWithPath:a[2]),settings:settings,commonFormat:.pcmFormatFloat32,interleaved:false)
guard let buffer=AVAudioPCMBuffer(pcmFormat:engine.manualRenderingFormat,frameCapacity:engine.manualRenderingMaximumFrameCount) else {fatalError("No buffer")}
player.scheduleFile(input,at:nil)
try engine.start();player.play()
let target=AVAudioFramePosition(ceil(Double(input.length)/Double(rate)))
var written:AVAudioFramePosition=0;var waits=0
while written<target {
 let count=AVAudioFrameCount(min(AVAudioFramePosition(buffer.frameCapacity),target-written))
 let status=try engine.renderOffline(count,to:buffer)
 switch status {
 case .success:
  try output!.write(from:buffer);written+=AVAudioFramePosition(buffer.frameLength)
 case .cannotDoInCurrentContext,.insufficientDataFromInputNode:
  waits+=1;if waits>10000 {fatalError("Offline render made no progress")}
 case .error:fatalError("Offline audio rendering failed")
 @unknown default:fatalError("Unknown render status")
 }
}
player.stop();engine.stop()
output=nil // Finalize WAV header before a top-level command-line process exits.
print("Rendered \(written) frames at \(format.sampleRate) Hz; rate \(rate), pitch 0")
