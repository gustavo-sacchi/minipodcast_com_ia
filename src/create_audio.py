from openai import OpenAI
import os
import io
import wave
import simpleaudio as sa
from dotenv import load_dotenv
load_dotenv()

class SpeechGenerator:
    def __init__(self, api_key: str, instructions = "Fale num tom alegre e positivo como um Youtuber Famoso.", model: str = "tts-1", voice="fable"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.voice = voice
        self.instructions = instructions

    def generate_speech(self, text, file_path):
        with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
                instructions=self.instructions,
                response_format="wav"
        ) as response:
            response.stream_to_file(file_path)

    def generate_wav_bytes(self, text: str) -> bytes:
        """
        Gera o áudio WAV em memória e retorna os bytes brutos.
        """
        buffer = io.BytesIO()
        with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
                instructions=self.instructions,
                response_format="wav"
        ) as response:
            data = response.read()  # lê TODOS os bytes de uma vez
            buffer.write(data)
        buffer.seek(0)
        return buffer.getvalue()

    def play_speech(self, text: str):
        """
        Gera o áudio em memória e já toca usando simpleaudio, sem salvar nada em disco.
        """
        wav_bytes = self.generate_wav_bytes(text)

        with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
            n_channels = wf.getnchannels()
            samp_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        play_obj = sa.play_buffer(frames, n_channels, samp_width, frame_rate)
        play_obj.wait_done()



def main():
    api_key = os.getenv("api_key")
    speech_generator = SpeechGenerator(api_key, voice="nova", model="gpt-4o-mini-tts")

    # text = "Olá Pessoal! Tudo bem com vocês? Comigo está Ótimo!"
    text = """Chegamos ao final de mais um tutorial épico! Hoje vocês viram como criar um grafo LangGraph completamente do zero para gerar mini podcasts automatizados!
Agora é com vocês! Peguem esse código, experimentem, quebrem, conserte, melhorem - é assim que a gente evolui! E não esqueçam: se conseguirem implementar alguma funcionalidade nova ou tiverem alguma dúvida, mandem nos comentários que eu respondo pessoalmente.
Se esse conteúdo agregou valor para vocês, deixem aquele LIKE maroto, se inscrevam no canal e ativem o sininho - vocês não vão querer perder os próximos tutoriais de IA que estão vindo por aí!
E lembrem-se: na era da inteligência artificial, quem não se adapta, fica para trás. Vocês acabaram de dar um passo gigante rumo ao futuro!
Nos vemos no próximo vídeo, galera! Tchau!"""

    speech_file_path = "final.WAV"
    speech_generator.generate_speech(text, speech_file_path)

    # speech_generator.play_speech(text)
    print("----Success----")


if __name__ == '__main__':
    main()