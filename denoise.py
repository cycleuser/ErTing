import sys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from pydub import AudioSegment
import os

def ai_denoise(input_file):
    # 1. 自动将 MP4/MP3 等格式转换为模型需要的 16k 采样率 WAV 格式
    temp_wav = "temp_input.wav"
    output_file = input_file.rsplit('.', 1)[0] + "_AI_clean.wav"
    
    print(f"🔄 正在转换音频格式...")
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(temp_wav, format="wav")

    # 2. 调用阿里的 AI 语音降噪模型
    print("🤖 正在调用 AI 模型进行降噪（首次运行会自动下载模型，请耐心等待）...")
    ans = pipeline(
        Tasks.acoustic_noise_suppression, 
        model='iic/speech_zipenhancer_ans_multiloss_16k_base'
    )
    ans(temp_wav, output_path=output_file)

    # 3. 清理临时文件
    os.remove(temp_wav)
    print(f"✅ 降噪完成！输出文件为: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 请在命令后加上你的音频/视频文件路径，例如：python denoise.py input.mp4")
    else:
        ai_denoise(sys.argv[1])
