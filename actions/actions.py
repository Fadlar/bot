import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from rapidfuzz import process, fuzz
import logging

API_URL = "http://localhost:8001/api/rasa-chatbot"

# Inisialisasi logging
logging.basicConfig(level=logging.INFO)

# Peta hari dari Bahasa Indonesia ke Bahasa Inggris
HARI_MAPPING = {
    "senin": "monday",
    "selasa": "tuesday",
    "rabu": "wednesday",
    "kamis": "thursday",
    "jumat": "friday",
    "jum\'at": "friday",
    "sabtu": "saturday",
    "minggu": "sunday"
}

import requests
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from rapidfuzz import process, fuzz
import logging

API_URL = "http://localhost:8001/api/rasa-chatbot"

# Inisialisasi logging
logging.basicConfig(level=logging.INFO)

class JadwalOperasionalForm(Action):
    def name(self):
        return "jadwal_operasional_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # Cek apakah slot `nama_layanan` sudah terisi
        nama_layanan = tracker.get_slot("nama_layanan")

        # Jika slot `nama_layanan` kosong, tanyakan nama layanan ke pengguna
        if not nama_layanan:
            dispatcher.utter_message(response="utter_ask_nama_layanan")
            return [SlotSet("nama_layanan", None)]

        # Jika `nama_layanan` sudah ada, lakukan validasi
        try:
            response = requests.get(f"{API_URL}/services")
            response.raise_for_status()
            layanan_tersedia = response.json()
        except requests.RequestException:
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil data layanan.")
            return [SlotSet("nama_layanan", None)]

        # Normalisasi layanan yang tersedia dan lakukan pencocokan fuzzy
        normalized_services = {service.lower(): service for service in layanan_tersedia}
        nama_layanan_input = nama_layanan.lower().strip()
        
        # Exact match atau fuzzy matching
        best_match_original = normalized_services.get(nama_layanan_input)
        if not best_match_original:
            result = process.extractOne(nama_layanan_input, list(normalized_services.keys()), scorer=fuzz.ratio)
            if result and result[1] >= 70:  # Threshold pencocokan fuzzy
                best_match_original = normalized_services[result[0]]
        
        if not best_match_original:
            return [SlotSet("nama_layanan", None)]
        
        # Slot `nama_layanan` berhasil divalidasi
        return [SlotSet("nama_layanan", best_match_original), FollowupAction("action_submit_jam_operasional")]

class ActionSubmitJamOperasional(Action):
    def name(self) -> str:
        return "action_submit_jam_operasional"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        nama_layanan = tracker.get_slot("nama_layanan")
        tujuan_layanan = tracker.get_slot("tujuan_layanan")

        if tujuan_layanan == "jam_operasional":
            # Logika untuk menampilkan jam operasional
            self.jam_operasional(dispatcher, tracker)
        elif tujuan_layanan == "info_layanan":
            # Logika untuk menampilkan info layanan
            dispatcher.utter_message(text=f"Berikut info layanan untuk layanan {nama_layanan}.")
        else:
            dispatcher.utter_message(text="Silakan ulangi pertanyaan Anda.")
        
        return []

    def jam_operasional(self, dispatcher: CollectingDispatcher, tracker: Tracker) -> list:
        nama_layanan = tracker.get_slot("nama_layanan")
        hari_input = tracker.get_slot("hari")

        if not nama_layanan:
            dispatcher.utter_message(response="utter_ask_nama_layanan")
            return []

        url = f"{API_URL}/schedules?service_name={nama_layanan}"
        try:
            jadwal_response = requests.get(url)
            jadwal_response.raise_for_status()
            data = jadwal_response.json()

            if not data:
                dispatcher.utter_message(text="Maaf, jadwal untuk layanan tersebut tidak ditemukan.")
                return []

            if hari_input and hari_input.lower() in HARI_MAPPING:
                hari_en = HARI_MAPPING[hari_input.lower()]
                start_time = data.get(f"{hari_en}_start", None)
                end_time = data.get(f"{hari_en}_end", None)

                if start_time != None and end_time != None:
                    dispatcher.utter_message(
                        response="utter_jadwal_harian",
                        nama_layanan=nama_layanan,
                        hari=hari_input.capitalize(),
                        jadwal=f"{start_time} - {end_time}"
                    )
                else:
                    dispatcher.utter_message(
                        text=f"Maaf, {nama_layanan} tidak buka pada hari {hari_input.capitalize()}."
                    )
            else:                
                jadwal_mingguan = "\n".join(
                    f"{day.capitalize()}: {self.format_jam(data.get(f'{day_id}_start', None))} - {self.format_jam(data.get(f'{day_id}_end', None))}"
                    if data.get(f'{day_id}_start') and data.get(f'{day_id}_end') else
                    f"{day.capitalize()}: Sedang tutup."
                    for day, day_id in HARI_MAPPING.items()
                )

                dispatcher.utter_message(
                    response="utter_jadwal_mingguan",
                    nama_layanan=nama_layanan,
                    jadwal_mingguan=jadwal_mingguan
                )
      
        except requests.RequestException:
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil data jadwal.")
        
        return []

    def format_jam(self, jam):
        if not jam:
            return "Tutup"  # Ganti dengan "Tutup" jika jam kosong atau None
        return jam[:5]
        

