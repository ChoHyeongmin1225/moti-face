import os
import threading
import pyaudio
import pvporcupine
import struct
from dotenv import load_dotenv

class HotwordDetector(threading.Thread):
    def __init__(self, hotword_queue):
        super().__init__(daemon=True)
        self.hotword_queue = hotword_queue
        self.listen_event = threading.Event()
        self.should_run = True
        self.pa = pyaudio.PyAudio()
        self.audio_stream = None
        self.is_listening = False
        
        load_dotenv(dotenv_path='./.env.local')

        access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        hotword_path = os.getenv("HOTWORD_PATH")
        model_path = os.getenv("MODEL_PATH")
        
        if not all([access_key, hotword_path, model_path]):
            print("오류: .env.local 필수 변수가 누락되었습니다.")
            self.should_run = False
            return

        self.device_index = None
        device_name_to_find = os.getenv("INPUT_DEVICE_NAME")
        if device_name_to_find:
            print(f"지정된 마이크 검색 중: '{device_name_to_find}'...")
            for i in range(self.pa.get_device_count()):
                device_info = self.pa.get_device_info_by_index(i)
                if device_info.get('maxInputChannels') > 0:
                    if device_name_to_find.lower() in device_info.get('name').lower():
                        self.device_index = i
                        print(f"🎚️  마이크를 찾았습니다: [{i}] {device_info.get('name')}")
                        break
            if self.device_index is None:
                print(f"⚠️  '{device_name_to_find}' 마이크를 찾을 수 없습니다. 시스템 기본 마이크를 사용합니다.")
        else:
            print("🎚️  시스템 기본 마이크를 사용합니다.")

        try:
            self.porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[hotword_path], model_path=model_path)
        except pvporcupine.PorcupineError as e:
            print(f"Porcupine 초기화 오류: {e}")
            self.should_run = False

    def run(self):
        if not self.should_run: return
        print("Hotword detector thread is ready.")
        
        while self.should_run:
            self.listen_event.wait() # 1. start_detection()이 호출되어 신호가 올 때까지 대기
            if not self.should_run: break
            
            # 2. 신호가 오면, 스레드 스스로 오디오 스트림을 연다
            self._start_listening()
            
            # 3. 감지 중지 신호가 오거나, 프로그램 종료 신호가 올 때까지 계속 감지
            while self.listen_event.is_set() and self.should_run:
                try:
                    pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    if self.porcupine.process(pcm) >= 0:
                        print("핫워드 감지됨! '안녕 모티'")
                        self.hotword_queue.put("hotword_detected")
                        self.listen_event.clear() # 감지했으니 스스로 중지 신호를 보냄
                except (IOError, struct.error):
                    # 스트림이 닫히는 과정에서 발생하는 오류는 무시
                    pass
                except Exception as e:
                    print(f"오디오 처리 중 오류: {e}")
                    self.listen_event.clear()
            
            # 4. 감지가 끝나면, 스레드 스스로 오디오 스트림을 닫는다
            self._stop_listening()

        if self.porcupine: self.porcupine.delete()
        self.pa.terminate()
        print("Hotword detector thread stopped.")

    def _start_listening(self):
        if not self.is_listening and self.should_run:
            try:
                self.audio_stream = self.pa.open(rate=self.porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=self.porcupine.frame_length, input_device_index=self.device_index)
                self.is_listening = True
                print("오디오 스트림 시작. 핫워드 감지 중.")
            except Exception as e:
                print(f"오디오 스트림 열기 실패: {e}")

    def _stop_listening(self):
        if self.is_listening and self.audio_stream:
            self.is_listening = False # 중요: 플래그를 먼저 변경
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            print("오디오 스트림 중지. 핫워드 감지 대기 중.")

    def start_detection(self):
        # 메인 스레드는 '감지 시작해!' 신호만 보낸다.
        self.listen_event.set()

    def stop_detection(self):
        # 메인 스레드는 '감지 중지해!' 신호만 보낸다.
        self.listen_event.clear()

    def stop(self):
        # 메인 스레드는 '프로그램 종료!' 신호만 보낸다.
        self.should_run = False
        self.listen_event.set()
        self.join()