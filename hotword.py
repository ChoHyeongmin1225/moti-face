# hotword.py

import pvporcupine
import pyaudio
import struct
import threading
import time
import queue
import os
from dotenv import load_dotenv

class HotwordDetector(threading.Thread):
    def __init__(self, access_key, hotword_queue):
        super().__init__()
        self.access_key = access_key
        self.hotword_queue = hotword_queue
        self.listen_event = threading.Event()
        self.should_run = True
        
        # 수정된 부분: 환경 변수에서 경로를 안전하게 로드하고, 파일 존재 여부를 확인하는 로직을 추가했습니다.
        load_dotenv(dotenv_path='./.env.local')

        hotword_path = os.getenv("HOTWORD_PATH")
        model_path = os.getenv("MODEL_PATH")
        
        if hotword_path is None or model_path is None:
            print("오류: .env.local 파일에서 'HOTWORD_PATH' 또는 'MODEL_PATH'를 찾을 수 없습니다.")
            self.porcupine = None
            self.should_run = False
            return
        
        if not os.path.exists(hotword_path):
            print(f"오류: 핫워드 파일 경로가 잘못되었습니다. '{hotword_path}' 파일을 찾을 수 없습니다.")
            self.porcupine = None
            self.should_run = False
            return

        if not os.path.exists(model_path):
            print(f"오류: 모델 파일 경로가 잘못되었습니다. '{model_path}' 파일을 찾을 수 없습니다.")
            self.porcupine = None
            self.should_run = False
            return
        
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[hotword_path],
                model_path=model_path
            )
        except pvporcupine.PorcupineError as e:
            print(f"Porcupine 초기화 오류: {e}")
            self.porcupine = None
            self.should_run = False
            return
        
        self.pa = pyaudio.PyAudio()
        self.audio_stream = None
        self.is_listening = False

    def run(self):
        if not self.should_run:
            return

        print("Hotword detector thread is ready.")

        while self.should_run:
            self.listen_event.wait()
            
            if not self.is_listening and self.should_run:
                self._start_listening()
            
            try:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    print("핫워드 감지됨! '안녕 모티'")
                    self.hotword_queue.put("hotword_detected")
            except Exception as e:
                if not self.should_run:
                    break
                if self.is_listening:
                    print(f"오디오 스트림 읽기 오류: {e}")
                self._stop_listening()
        
        if self.porcupine:
            self.porcupine.delete()
        if self.pa:
            self.pa.terminate()

    def _start_listening(self):
        if not self.is_listening:
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            self.is_listening = True
            print("오디오 스트림 시작. 핫워드 감지 중.")

    def _stop_listening(self):
        if self.is_listening:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.is_listening = False
            print("오디오 스트림 중지. 핫워드 감지 대기 중.")

    def start_detection(self):
        self.listen_event.set()

    # 수정된 부분: stop_detection() 메서드를 더 안전하게 수정하여, 이미 닫힌 스트림에 접근하지 않도록 했습니다.
    def stop_detection(self):
        self.listen_event.clear()
        if self.audio_stream is not None:
             self._stop_listening()

    def stop(self):
        self.should_run = False
        self.listen_event.set() 
        self.join()