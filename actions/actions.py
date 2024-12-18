import logging
from typing import Any, Dict, Text

import requests
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

API_URL = "http://localhost:8000/api/rasa-chatbot"

# Inisialisasi logging
MAX_LENGTH = 200
ALLOWED_HARI = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]

class ActionSetIdLayanan(Action):
    def name(self) -> str:
        return "action_set_id_layanan"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        # Ambil metadata dari tracker
        metadata = tracker.latest_message.get("metadata", {})

        # Cek apakah metadata mengandung id_layanan
        # id_layanan = 28
        id_layanan = metadata.get("id_layanan")

        logging.info(id_layanan)

        if id_layanan: 
            return [SlotSet("id_layanan", id_layanan)]
        else:
            return []

class ValidateCekStatusAntrianForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_cek_status_antrian_form"
    
    def validate_nomor_antrian(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        """
        Validasi slot nomor_antrian memastikan bahwa input memiliki format yang benar
        (misalnya A001, B002, atau 001) dan mengubahnya ke format angka (001, 002, dll.)
        """
        import re

        # memastikan input sesuai format (A001, B002 atau hanya angka seperti 001)
        match = re.match(r"^(?:[A-Z](\d{3})|(\d{3}))$", slot_value.upper())

        if match:
            # ekstrak angka (001, 002) dari input
            formated_number = match.group(1) if match.group(1) else match.group(2)
            return {"nomor_antrian": formated_number}
        
        # jika format salah, maka minta ulang input
        dispatcher.utter_message(text="Format nomor antrian tidak valid. Silahkan masukan format seperti A001, B002, atau 001")
        return {"nomor_antrian": None}

class ActionManageServices(Action):
    def name(self) -> str:
        return "action_manage_services"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        tujuan_layanan = tracker.get_slot("tujuan_layanan")

        if tujuan_layanan in ["informasi", "persyaratan", "mekanisme_prosedur", "waktu_tunggu","tarif_biaya"]:
            self.informasi_response(dispatcher, tracker, tujuan_layanan)
        elif tujuan_layanan == "jam_operasional":
            self.jam_operasional(dispatcher, tracker)
        elif tujuan_layanan == "cek_antrian":
            self.cek_antrian(dispatcher, tracker)
        elif tujuan_layanan == "cek_status_antrian":
            self.cek_status_antrian(dispatcher, tracker)
        else:
            dispatcher.utter_message(text="Silakan ulangi pertanyaan Anda.")

        return []

    def jam_operasional(self, dispatcher: CollectingDispatcher, tracker: Tracker) -> list:
        id_layanan = tracker.get_slot("id_layanan")


        url = f"{API_URL}/schedules/{id_layanan}"
        try:
            jadwal_response = requests.get(url)
            jadwal_response.raise_for_status()
            data = jadwal_response.json()

            message = f"Berikut jam operasional untuk **{data['service_name']}**:\n"
            message += f"\- Senin: **{data['monday']}**\n"
            message += f"\- Selasa: **{data['tuesday']}**\n"
            message += f"\- Rabu: **{data['wednesday']}**\n"
            message += f"\- Kamis: **{data['thursday']}**\n"
            message += f"\- Jum'at: **{data['friday']}**\n"
            message += f"\- Sabtu: **{data['saturday']}**\n"
            message += f"\- Minggu: **{data['sunday']}**\n"
            message += "Jika ada pertanyaa lebih lanjut, jangan ragu untuk menghubungi kami!"

            dispatcher.utter_message(text=message)
            return []

        except requests.RequestException:
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil data jadwal.")
        
        return []
    
    def informasi_response(self, dispatcher: CollectingDispatcher, tracker: Tracker, tipe_info_layanan: Text):
        id_layanan = tracker.get_slot("id_layanan")
        # URL untuk mengambil data dari API
        url = f"{API_URL}/services/{id_layanan}"

        # mapping tipe informasi layanan dengan kolom yang sesuai dari response
        mapping_tipe_info = {
            "informasi": "description",
            "persyaratan": "requirements",
            "mekanisme_prosedur": "procedure",
            "waktu_tunggu": "time_period",
            "tarif_biaya": "tariff"
        }

        # mengecek apakah tipe informasi yang diminta valid
        if tipe_info_layanan not in mapping_tipe_info:
            dispatcher.utter_message(text="Tipe informasi layanan yang Anda minta tidak valid.")
            return []

        try:
            # mengambil data dari API
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # ambil kolom layanan yang sesuai berdasarkan tipe informasi layanan
            konten = self.clean_media_tags_and_truncate(data.get(mapping_tipe_info[tipe_info_layanan], "Informasi tidak tersedia"))

            # menyusun pesan dengan URL detail
            urlDetail = f"/service/{id_layanan}/{mapping_tipe_info[tipe_info_layanan].replace('_', '-')}"
            message = f"Berikut {tipe_info_layanan.replace('_',' ')} untuk layanan {data['name']}:\n"
            message += konten
            message += f"\nUntuk lebih detailnya anda bisa <a href='{urlDetail}'>lihat disini.</a>\n"
            message += "Jika ada hal lain yang ingin Anda tanyakan, silahkan sampaikan! 😊"

            dispatcher.utter_message(text=message)
            return []

        except requests.RequestException:
            # Tangani kesalahan API
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil informasi.")
            return []

        except Exception as e:
            # Tangani kesalahan lainnya
            dispatcher.utter_message(text="Terjadi kesalahan yang tidak terduga.")
            return []

    def cek_antrian(self, dispatcher: CollectingDispatcher, tracker: Tracker) -> list:
        id_layanan = tracker.get_slot('id_layanan')
        url = f"{API_URL}/general-queues/{id_layanan}"

        try:
            antrian_response = requests.get(url)
            antrian_response.raise_for_status()
            data = antrian_response.json()

            if not data:
                dispatcher.utter_message(text=f"Maaf, tidak ada antrian untuk layanan {data['service_name']} hari ini.")
                return []

            message = f"Berikut informasi antrian untuk layanan **{data['service_name']}**:\n"
            message += f"\- Kuota antrian: **{data['quota']}**\n"
            message += f"\- Total antrian: **{data['total']}**\n"
            message += f"\- Antrian belum dilayani: **{data['belum_dilayani']}**\n"
            message += f"\- Antrian sudah dipanggil: **{data['sudah_dipanggil']}**\n"
            message += f"\- Antrian sedang dilayani: **{data['sedang_dilayani']}**\n"
            message += f"\- Antrian selesai: **{data['selesai']}**\n"
            message += f"\- Antrian tidak datang: **{data['tidak_datang']}**\n"
            message += f"Silahkan sebutkan nomor antrian dan nama layanan jika anda ingin mengetahui status antrian hari ini."

            dispatcher.utter_message(message)
            return []

        except requests.RequestException:
            # Tangani kesalahan API
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil data antrian.")
            return []

        except Exception as e:
            # Tangani kesalahan lainnya
            dispatcher.utter_message(text="Terjadi kesalahan yang tidak terduga.")
            return []
        
    def cek_status_antrian(self, dispatcher: CollectingDispatcher, tracker: Tracker) -> list:
        id_layanan = tracker.get_slot('id_layanan')
        nomor_antrian = tracker.get_slot('nomor_antrian')
        url = f"{API_URL}/check-queue-status/{id_layanan}?queue_number={nomor_antrian}"

        try:
            antrian_response = requests.get(url)
            antrian_response.raise_for_status()
            data = antrian_response.json()
            
            if data['status'] == 'notfound':
                dispatcher.utter_message(text=f"Maaf, antrian {nomor_antrian} tidak ditemukan di layanan **{data['service_name']}** hari ini.")
                return []

            message = f"Berikut adalah informasi status antrian Anda:\n"
            message += f" \- Nomor antrian: **{data['queue_number']}**\n"
            message += f" \- Status antrian: **{data['status'].capitalize()}**\n"
            message += f"Jika ada hal lain yang ingin Anda tanyakan, silakan sampaikan! 😊"

            dispatcher.utter_message(message)
            return []

        except requests.RequestException:
            # Tangani kesalahan API
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil data antrian.")
            return []

        except Exception as e:
            # Tangani kesalahan lainnya
            logging.error(e)
            dispatcher.utter_message(text="Terjadi kesalahan yang tidak terduga.")
            return []

    def clean_media_tags_and_truncate(self,text, max_length=600):
        import re
        """
        Membersihkan elemen media, tag kosong, dan memotong teks jika melebihi panjang maksimum,
        tanpa memotong di tengah-tengah tag HTML.
        """
        # Hapus elemen media seperti <img>, <svg>, dll.
        media_pattern = r"<(img|svg|video|audio|iframe|embed|object)[^>]*>.*?</\1>|<(img|svg|video|audio|iframe|embed|object)[^>]*\/?>"
        cleaned_text = re.sub(media_pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

        # Hapus tag kosong atau hanya berisi whitespace (&nbsp;)
        empty_tag_pattern = r"<(\w+)[^>]*>(\s|&nbsp;)*</\1>"
        cleaned_text = re.sub(empty_tag_pattern, "", cleaned_text, flags=re.IGNORECASE)

        # Pastikan tidak memotong di tengah tag HTML
        if len(cleaned_text) > max_length:
            visible_text = ""
            length = 0
            for match in re.finditer(r"[^<]+|<[^>]+>", cleaned_text):  # Cocokkan teks atau tag HTML
                token = match.group()
                if token.startswith("<"):  # Jika token adalah tag HTML
                    visible_text += token
                else:  # Jika token adalah teks biasa
                    if length + len(token) > max_length:
                        visible_text += token[:max_length - length] + "..."
                        break
                    visible_text += token
                    length += len(token)
            return visible_text

        return cleaned_text

class ActionRecordFeedback(Action):
    def name(self) -> str:
        return "action_record_feedback"

    def run(self, dispatcher: CollectingDispatcher, tracker, domain) -> list:
        # Mengambil feedback dari pesan terakhir pengguna
        feedback = tracker.latest_message.get("text")

        # Simpan feedback ke database atau log jika perlu
        # Di sini, Anda bisa menambahkan logika untuk menyimpan ke database
        # Contoh: simpan ke variabel slot atau sistem lain

        # Memberikan respons konfirmasi ke pengguna
        dispatcher.utter_message(text=f"Terima kasih atas feedback Anda: {feedback}")
        
        return []
