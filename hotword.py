# hotword.py

import pvporcupine
import pyaudio
import struct
import threading
import os
from dotenv import load_dotenv

class HotwordDetector(threading.Thread):
    # HotwordDetector 클래스는 스레드로 동작하여 메인 프로그램과 별도로 핫워드 감지 작업을 수행합니다.
    def __init__(self, access_key, hotword_queue):
        super().__init__()
        self.access_key = access_key

        # 핫워드 감지 시 메인 스레드에 메시지를 전달하기 위한 큐입니다
        # 스레드에게 핫워드 감지를 시작하라고 알리는 데 사용되는 이벤트 객체입니다.
        # 스레드가 계속 실행되어야 하는지 여부를 결정하는 플래그입니다.
        self.hotword_queue = hotword_queue
        self.listen_event = threading.Event()
        self.should_run = True

        load_dotenv(dotenv_path='./.env.local')

        # 환경 변수에서 핫워드 및 파라미터 파일 경로를 불러옵니다.
        hotword_path = os.getenv("HOTWORD_PATH")
        model_path = os.getenv("MODEL_PATH")
        
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
                # The exception is expected when the stream is closed
                if not self.should_run:
                    break
                # Only print the error if it's not due to normal shutdown
                if self.is_listening:
                    print(f"오디오 스트림 읽기 오류: {e}")
                self._stop_listening()
        
        # Final cleanup on thread exit
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

    def stop_detection(self):
        self.listen_event.clear()

        if self.audio_stream is not None:
             self._stop_listening()

    def stop(self):
        """Signals the thread to stop and waits for it to finish."""
        self.should_run = False
        # Unblock the wait() call
        self.listen_event.set() 
        # Wait for the thread to finish its loop
        self.join()