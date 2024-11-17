import requests
from typing import Text, Any, Dict
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from rapidfuzz import process, fuzz
from rasa_sdk.types import DomainDict
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
    "sabtu": "saturday",
    "minggu": "sunday"
}

ALLOWED_HARI = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]


class BaseValidateForm(FormValidationAction):
    def name(self) -> Text:
        # Default jika belum diimplementasikan
        return "base_validate_form"
    
    def validate_nama_layanan(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        # Ambil daftar layanan dari API
        daftar_layanan = self.get_layanan_dari_api()

        # Normalisasi layanan dalam bentuk kamus untuk pencocokan
        normalized_services = {service.lower(): service for service in daftar_layanan}

        # Ambil input mentah jika slot_value kosong
        input_user = slot_value if slot_value else tracker.latest_message.get("text")
        nama_layanan_input = input_user.lower().strip()

        # Cek exact match
        best_match_original = normalized_services.get(nama_layanan_input)

        # Jika tidak ada exact match, lakukan fuzzy matching
        if not best_match_original:
            result = process.extractOne(nama_layanan_input, list(normalized_services.keys()), scorer=fuzz.ratio)
            if result and result[1] >= 70:  # Threshold fuzzy matching
                best_match_original = normalized_services[result[0]]

        # Jika tidak ditemukan match
        if not best_match_original:
            dispatcher.utter_message(text=f"Maaf, layanan '{input_user}' tidak ditemukan. Silakan coba lagi.")
            return {"nama_layanan": None}

        # Slot `nama_layanan` berhasil divalidasi
        return {"nama_layanan": best_match_original}

    def get_layanan_dari_api(self):
        # Ambil daftar layanan dari API
        response = requests.get(f"{API_URL}/services")
        if response.status_code == 200:
            return response.json()
        return []
    
    def validate_hari(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        """Validate `hari` value"""
        if slot_value not in ALLOWED_HARI:
            dispatcher.utter_message(
                text=f"Hari yang anda input tidak valid. Coba sebutkan {','.join(ALLOWED_HARI)}."
            )
            return {"hari": None}
        return {"pizza_type": slot_value}

class ValidateJamOperasionalForm(BaseValidateForm):
    def name(self) -> Text:
        return "validate_jam_operasional_form"

class ValidateInformasiForm(BaseValidateForm):
    def name(self) -> Text:
        return "validate_informasi_form"
    
class ValidatePersyaratanForm(BaseValidateForm):
    def name(self) -> Text:
        return "validate_persyaratan_form"

class ValidateMekanismeProsedurForm(BaseValidateForm):
    def name(self) -> Text:
        return "validate_mekanisme_prosedur_form"

class ValidateWaktuTungguForm(BaseValidateForm):
    def name(self) -> Text:
        return "validate_waktu_tunggu_form"

class ValidateTarifBiayaForm(BaseValidateForm):
    def name(self) -> Text:
        return "validate_tarif_biaya_form"

class ValidateNamaLayananTersediaForm(BaseValidateForm):
    def name(self) -> Text:
        return "validate_nama_layanan_tersedia_form"

class ActionManageServices(Action):
    def name(self) -> str:
        return "action_manage_services"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        nama_layanan = tracker.get_slot("nama_layanan")
        tujuan_layanan = tracker.get_slot("tujuan_layanan")

        if tujuan_layanan == "jam_operasional":
            # Logika untuk menampilkan jam operasional
            self.jam_operasional(dispatcher, tracker)
        elif tujuan_layanan == "informasi":
            # Logika untuk menampilkan info layanan
            dispatcher.utter_message(text=f"Berikut informasi untuk layanan {nama_layanan}.")
        elif tujuan_layanan == "persyaratan":
            # Logika untuk menampilkan info layanan
            dispatcher.utter_message(text=f"Berikut persyaratan untuk layanan {nama_layanan}.")
        elif tujuan_layanan == "mekanisme_prosedur":
            # Logika untuk menampilkan info layanan
            dispatcher.utter_message(text=f"Berikut mekanisme prosedur untuk layanan {nama_layanan}.")
        elif tujuan_layanan == "waktu_tunggu":
            # Logika untuk menampilkan info layanan
            dispatcher.utter_message(text=f"Berikut waktu tunggu untuk layanan {nama_layanan}.")
        elif tujuan_layanan == "tarif_biaya":
            # Logika untuk menampilkan info layanan
            dispatcher.utter_message(text=f"Berikut tarif biaya untuk layanan {nama_layanan}.")
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

                if start_time is not None and end_time is not None:
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
                dispatcher.utter_message(text="Hari yang dimasukkan tidak valid.")
        
        except requests.RequestException:
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil data jadwal.")
        
        return []


    def format_jam(self, jam):
        if not jam:
            return "Tutup"  # Ganti dengan "Tutup" jika jam kosong atau None
        return jam[:5]


    # def validate_hari(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
    #     """Validate `hari`"""
    #     return {"hari": slot_value}