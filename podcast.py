from dotenv import load_dotenv
load_dotenv()

from src.graph import app
from src.create_audio import SpeechGenerator
import os
import io
from pydub import AudioSegment
from pydub.playback import play


class PodcastGenerator:
    def __init__(self, api_key: str):
        self.apresentador = SpeechGenerator(
            api_key,
            voice="sage",
            instructions="Você é uma apresentadora de podcast. Por isso fale num tom alegre e positivo como uma apresentadora."
        )
        self.especialista = SpeechGenerator(
            api_key,
            voice="alloy",
            instructions="Você é um expert que está sendo entrevistado. "
        )

    def generate_audio_segment(self, text: str, speaker_type: str) -> AudioSegment:
        """
        Gera um segmento de áudio em memória e retorna como AudioSegment
        """
        if speaker_type == "apresentador":
            wav_bytes = self.apresentador.generate_wav_bytes(text)
        else:
            wav_bytes = self.especialista.generate_wav_bytes(text)

        # Converte bytes para AudioSegment
        audio_segment = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        return audio_segment

    def generate_podcast_file(self, roteiro, output_file: str = "podcast_completo.wav"):
        """
        Gera o arquivo de podcast completo concatenando todos os áudios
        """
        print("Gerando áudios e concatenando...")

        # Lista para armazenar todos os segmentos
        audio_segments = []

        # Adiciona uma pequena pausa entre falas (0.5 segundos de silêncio)
        pause = AudioSegment.silent(duration=500)

        for i, mensagem in enumerate(roteiro):
            if mensagem.name is None:
                print(f"Processando fala {i + 1}/{len(roteiro)}: [ENTREVISTADOR]")
                speaker_type = "apresentador"
            else:
                print(f"Processando fala {i + 1}/{len(roteiro)}: [ESPECIALISTA]")
                speaker_type = "especialista"

            # Gera o áudio para esta fala
            audio_segment = self.generate_audio_segment(mensagem.content, speaker_type)
            audio_segments.append(audio_segment)

            # Adiciona pausa entre falas (exceto na última)
            if i < len(roteiro) - 1:
                audio_segments.append(pause)

        # Concatena todos os segmentos
        print("Concatenando áudios...")
        if not audio_segments:
            raise ValueError("Nenhum áudio foi gerado!")

        podcast_completo = audio_segments[0]
        for segment in audio_segments[1:]:
            podcast_completo += segment

        # Salva o arquivo final
        print(f"Salvando arquivo: {output_file}")
        podcast_completo.export(output_file, format="wav")

        return output_file

    def play_podcast_file(self, file_path: str):
        """
        Reproduz o arquivo de podcast completo
        """
        print(f"Reproduzindo podcast: {file_path}")
        audio = AudioSegment.from_wav(file_path)
        play(audio)


def main(topico: str, entrevistado: str, podcast_file: str):
    # Verifica se já existe um arquivo de podcast
    podcast_file = podcast_file

    if os.path.exists(podcast_file):
        print(f"Arquivo de podcast encontrado: {podcast_file}")
        choice = input("Deseja reproduzir o podcast existente? (s/n): ").lower()

        if choice == 's':
            api_key = os.getenv("api_key")
            generator = PodcastGenerator(api_key)
            generator.play_podcast_file(podcast_file)
            return

    # Gera novo podcast
    print("Gerando novo podcast...")
    podcast = app.invoke({"topico": topico, "entrevistado": entrevistado})

    api_key = os.getenv("api_key")
    generator = PodcastGenerator(api_key)

    # Gera o arquivo de podcast completo
    output_file = generator.generate_podcast_file(podcast["roteiro_final"], podcast_file)

    # Pergunta se quer reproduzir agora
    choice = input("Deseja reproduzir o podcast agora? (s/n): ").lower()
    if choice == 's':
        generator.play_podcast_file(output_file)

    print("Podcast salvo com sucesso!")


if __name__ == '__main__':
    main(topico= "Viagens pelo mundo. Conhecendo lugares inimagináveis.",
         entrevistado= "Influencer: Sara, do canal Viagens da Sara.",
         podcast_file="Viagem.wav")
