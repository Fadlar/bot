# actions.py
from rasa_sdk.types import DomainDict
import requests
import logging

from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Coroutine, Text, Dict, List
from fuzzywuzzy import process
from datetime import datetime

API_URL = "http://localhost:8001/api/rasa-chatbot" 

# Inisialisasi logging
logging.basicConfig(level=logging.INFO)

class ActionProvideServiceType(Action):
    def name(self) -> Text:
        return "action_provide_service_type"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # service type list
        service_type_list = ["informasi layanan", "jadwal operasional", "cek antrian", "buat antrian"]
        # mendapatkan input dari slot
        service_type = tracker.get_slot('service_type')

        if service_type:
            matched_service_type, score = process.extractOne(service_type, service_type_list)

            if score >= 70:
                if matched_service_type == "informasi layanan":
                    return [SlotSet("service_type_selected", matched_service_type)]
                elif matched_service_type == "jadwal operasional":
                    return [SlotSet("service_type_selected", matched_service_type)]
                elif matched_service_type == "cek antrian":
                    return [SlotSet("service_type_selected", matched_service_type)]
                elif matched_service_type == "buat antrian":
                    return [SlotSet("service_type_selected", matched_service_type)]
                else:
                    dispatcher.utter_message(text="Informasi yang diminta tidak tersedia.")
                    return []
            else: 
                dispatcher.utter_message(text=f"Maaf, saya tidak menemukan kecocokan yang memadai untuk informasi '{service_type}'. Mohon coba dengan kata lain.")
                return []
        else:
            dispatcher.utter_message("Informasi yang diminta tidak tersedia")
            return []

class ActionProvideService(Action):
    def name(self) -> Text:
        return "action_provide_service"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        service_name = tracker.get_slot('service_name')

        # Membuat panggilan API ke Laravel
        url = f"{API_URL}/services"
        try:
            response = requests.get(url)
            all_services = response.json()  # Mengambil semua layanan

            if response.status_code == 200:
                # Mengambil nama layanan dari response
                service_names = [service['name'] for service in all_services]

                # Menggunakan fuzzy wuzzy untuk mencocokan layanan
                matched_service, score = process.extractOne(service_name, service_names)
                if score >= 90:
                    # Kecocokan sempurna ditemukan, set slot dan lanjutkan
                    return [SlotSet('matched_service', matched_service)]
                if score >= 70:
                    # Kecocokan sebagian, minta konfirmasi
                    # confirmation_message = f"Apakah Anda merujuk pada layanan **{matched_service}**? Mohon konfirmasi agar saya dapat memberikan informasi yang tepat."
                    # dispatcher.utter_message(text=confirmation_message)

                    # Simpan layanan yang cocok dalam slot untuk langkah selanjutnya
                    return [SlotSet('matched_service', matched_service)]
                else:
                    message = f"Tidak ada layanan yang cocok ditemukan untuk '{service_name}'. Apakah Anda ingin mencoba layanan lain?"
            else:
                message = "Tidak ada informasi layanan yang dapat diambil."
        except Exception as e:
            logging.error(f"Error saat menghubungi semua layanan: {e}")
            message = "Maaf, terjadi kesalahan saat menghubungi layanan. Silakan coba lagi nanti."

        dispatcher.utter_message(text=message)
        return []

class ActionProvideServiceInfo(Action):
    def name(self) -> Text:
        return "action_provide_service_info"
   
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Daftar opsi yang tersedia
        options = ["deskripsi", "persyaratan", "mekanisme prosedur", "jangka waktu", "biaya"]

        # Mendapatkan input dari slot
        matched_service = tracker.get_slot('matched_service')
        service_type_selected = tracker.get_slot('service_type_selected')
        service_info_option = tracker.get_slot('service_info_option')
        
        if service_type_selected:
            if service_type_selected == "":
                dispatcher.utter_message(text="Jenis layanan tidak ditentukan.")
                return []
            
        if matched_service and service_info_option:
            # Ambil data dari API
            url = f"{API_URL}/services/{matched_service}"
            service_info_option = service_info_option.lower().strip()

            try:
                response = requests.get(url)
                service = response.json()  # Mengambil info service
              
                if response.status_code == 200:
                    # Menggunakan fuzzy wuzzy untuk mencocokkan opsi informasi
                    matched_option, score = process.extractOne(service_info_option, options)
                    # Menentukan ambang batas 
                    if score >= 70:
                        if matched_option == "deskripsi":
                            info_to_display = service.get('description')
                            if info_to_display is None or info_to_display.strip() == "":
                                info_to_display = f"Deskripsi untuk {matched_service} tidak tersedia."
                        elif matched_option == "persyaratan":
                            info_to_display = service.get('requirements')
                            if info_to_display is None or info_to_display.strip() == "":
                                info_to_display = f"Persyaratan untuk {matched_service} tidak tersedia."
                        elif matched_option == "mekanisme prosedur":
                            info_to_display = service.get('procedure')
                            if info_to_display is None or info_to_display.strip() == "":
                                info_to_display = f"Mekanisme & prosedur untuk {matched_service} tidak tersedia."
                        elif matched_option == "jangka waktu":
                            info_to_display = service.get('time_period')
                            if info_to_display is None or info_to_display.strip() == "":
                                info_to_display = f"Jangka waktu penyelesaian untuk {matched_service} tidak tersedia."
                        elif matched_option == "biaya":
                            info_to_display = service.get('tariff')
                            if info_to_display is None or info_to_display.strip() == "":
                                info_to_display = f"Biaya atau tarif untuk {matched_service} tidak tersedia."
                        else:
                            info_to_display = "Informasi yang diminta tidak tersedia."

                        dispatcher.utter_message(text=f"Informasi **{matched_option}** untuk layanan **{matched_service}**:\n{info_to_display}")
                        return [SlotSet('matched_service', matched_service)]
                    else:
                        dispatcher.utter_message(text=f"Maaf, saya tidak menemukan kecocokan yang memadai untuk '{service_info_option}'. Mohon coba dengan kata lain.")
                else:
                    message = "Tidak ada informasi layanan yang dapat diambil."
                    dispatcher.utter_message(text=message)
            except Exception as e:
                logging.error(f"Error saat menghubungi layanan: {e}")
                message = "Maaf, terjadi kesalahan saat menghubungi layanan. Silakan coba lagi nanti."
                dispatcher.utter_message(text=message)
                return []

class ActionProvideServiceDirect(Action):
    def name(self) -> Text:
        return "action_provide_service_direct"
   
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Mendapatkan input layanan dan opsi dari slot
        service_name = tracker.get_slot('service_name')
        service_info_option = tracker.get_slot('service_info_option')

        if not service_name or not service_info_option:
            dispatcher.utter_message(text="Maaf, saya memerlukan nama layanan dan opsi informasi yang jelas. Silakan sebutkan kembali.")
            return []

        # Panggilan API untuk mendapatkan semua layanan
        try:
            url = f"{API_URL}/services"
            response = requests.get(url)
            all_services = response.json()

            if response.status_code == 200:
                # Mengambil nama layanan dari response
                service_names = [service['name'] for service in all_services]

                # Menggunakan fuzzy wuzzy untuk mencocokkan layanan
                matched_service, score = process.extractOne(service_name, service_names)
                if matched_service is not None:
                    if score >= 70:
                        # Jika layanan ditemukan, ambil detail layanan dari API
                        url_service_detail = f"{API_URL}/services/{matched_service}"
                        response_detail = requests.get(url_service_detail)
                        service_detail = response_detail.json()

                        if response_detail.status_code == 200:
                            # Daftar opsi informasi yang tersedia
                            options = ["deskripsi", "persyaratan", "mekanisme prosedur", "jangka waktu", "biaya"]

                            # Menggunakan fuzzy wuzzy untuk mencocokkan opsi informasi
                            matched_option, option_score = process.extractOne(service_info_option.lower().strip(), options)
                            if option_score >= 70:
                                # Menampilkan informasi berdasarkan opsi yang dipilih
                                if matched_option == "deskripsi":
                                    info_to_display = service_detail.get('description')
                                    if info_to_display is None or info_to_display.strip() == "":
                                        info_to_display = f"Deskripsi untuk {matched_service} tidak tersedia."
                                elif matched_option == "persyaratan":
                                    info_to_display = service_detail.get('requirements')
                                    if info_to_display is None or info_to_display.strip() == "":
                                        info_to_display = f"Persyaratan untuk {matched_service} tidak tersedia."
                                elif matched_option == "mekanisme prosedur":
                                    info_to_display = service_detail.get('procedure')
                                    if info_to_display is None or info_to_display.strip() == "":
                                        info_to_display = f"Mekanisme & prosedur untuk {matched_service} tidak tersedia."
                                elif matched_option == "jangka waktu":
                                    info_to_display = service_detail.get('time_period')
                                    if info_to_display is None or info_to_display.strip() == "":
                                        info_to_display = f"Jangka waktu penyelesaian untuk {matched_service} tidak tersedia."
                                elif matched_option == "biaya":
                                    info_to_display = service_detail.get('tariff')
                                    if info_to_display is None or info_to_display.strip() == "":
                                        info_to_display = f"Biaya atau tarif untuk {matched_service} tidak tersedia."
                                else:
                                    info_to_display = "Informasi yang diminta tidak tersedia."

                                dispatcher.utter_message(text=f"Informasi **{matched_option}** untuk layanan **{matched_service}**:\n{info_to_display}")
                                return [SlotSet('matched_service', matched_service)]

                            else:
                                dispatcher.utter_message(text=f"Maaf, saya tidak menemukan kecocokan yang memadai untuk opsi '{service_info_option}'. Mohon coba dengan kata lain.")
                                return [SlotSet('matched_service', matched_service)]
                        else:
                            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil detail layanan.")
                            return []

                    else:
                        dispatcher.utter_message(text=f"Tidak ada layanan yang cocok ditemukan untuk '{service_name}'. Silakan coba layanan lain.")
                        return []
                else:
                    dispatcher.utter_message(text=f"Mohon masukan layanan yang valid.")
                    return []
            else:
                dispatcher.utter_message(text="Maaf, saya tidak mengenali layanan tersebut. Mohon pastikan Anda memasukkan nama layanan yang valid atau silakan coba lagi dengan kata kunci yang berbeda.")
                return []

        except Exception as e:
            logging.error(f"Error saat menghubungi layanan: {e}")
            dispatcher.utter_message(text="Maaf, terjadi kesalahan saat menghubungi layanan. Silakan coba lagi nanti.")
            return []

class ActionProvideScheduleInfo(Action):
    def name(self) -> Text:
        return "action_provide_schedule_info"
   
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Daftar hari yang tersedia
        options = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]

        # Mendapatkan input dari slot
        matched_service = tracker.get_slot('matched_service')
        schedule_day = tracker.get_slot('schedule_day')

        # Mapping hari ke properti service
        day_mapping = {
            "senin": ("monday_start", "monday_end"),
            "selasa": ("tuesday_start", "tuesday_end"),
            "rabu": ("wednesday_start", "wednesday_end"),
            "kamis": ("thursday_start", "thursday_end"),
            "jumat": ("friday_start", "friday_end"),
            "sabtu": ("saturday_start", "saturday_end"),
            "minggu": ("sunday_start", "sunday_end"),
        }

        # Membuat panggilan API ke Laravel
        url = f"{API_URL}/schedules/{matched_service}"

        try:
            response = requests.get(url)
            service = response.json()  # Mengambil info service

            if response.status_code == 200:
                if schedule_day and matched_service:
                    schedule_day = schedule_day.lower().strip()
                    matched_day, score = process.extractOne(schedule_day, options)

                    if score >= 70 and matched_day in day_mapping:
                        start_prop, end_prop = day_mapping[matched_day]
                        start_time = service.get(start_prop)
                        end_time = service.get(end_prop)
                        if start_time and end_time:
                            schedule_info_to_display = f"{start_time} - {end_time}"
                        else:
                            schedule_info_to_display = "Sedang tutup/libur."
                        
                        dispatcher.utter_message(text=f"Jadwal operasional untuk layanan **{matched_service}** di hari **{matched_day.capitalize()}**: {schedule_info_to_display}")
                        return []
                    else:
                        # Jika hari tidak cocok, tampilkan seluruh jadwal
                        message = self.construct_full_schedule(service, matched_service)
                        dispatcher.utter_message(text=message)
                        return []
                elif not schedule_day and matched_service:
                    # Tampilkan seluruh jadwal
                    message = self.construct_full_schedule(service, matched_service)
                    dispatcher.utter_message(text=message)
                    return []
                
                elif schedule_day and not matched_service:
                    message = "Maaf, saya perlu tahu layanan apa yang Anda maksud. Bisakah Anda menyebutkan layanan tersebut agar saya bisa membantu Anda lebih baik?"
                    dispatcher.utter_message(text=message)
                    return []

                else:
                    message = "Maaf, saya perlu tahu layanan apa yang Anda maksud. Bisakah Anda menyebutkan layanan tersebut agar saya bisa membantu Anda lebih baik?"
                    dispatcher.utter_message(text=message)
                    return []
            else:
                message = "Tidak ada informasi layanan yang dapat diambil."
                dispatcher.utter_message(text=message)
                return []
        except Exception as e:
            logging.error(f"Error saat menghubungi layanan: {e}")
            message = "Maaf, terjadi kesalahan saat menghubungi layanan."
            dispatcher.utter_message(text=message)
            return []
    
    def construct_full_schedule(self, service: Dict, matched_service: Text) -> Text:
        day_mapping = {
                "senin": ("monday_start", "monday_end"),
                "selasa": ("tuesday_start", "tuesday_end"),
                "rabu": ("wednesday_start", "wednesday_end"),
                "kamis": ("thursday_start", "thursday_end"),
                "jumat": ("friday_start", "friday_end"),
                "sabtu": ("saturday_start", "saturday_end"),
                "minggu": ("sunday_start", "sunday_end")
            }
        
        schedule_lines = []
        for day, (start_prop, end_prop) in day_mapping.items():
            start_time = service.get(start_prop)
            end_time = service.get(end_prop)
            if start_time and end_time:
                schedule = f"{start_time} - {end_time}"
            else:
                schedule = "Sedang tutup/libur."
            schedule_lines.append(f"- {day.capitalize()}: {schedule}")

        message = f"""Berikut jadwal operasional layanan **{matched_service}**:
{chr(10).join(schedule_lines)}

Semoga informasi ini membantu! Jika ada hal lain yang ingin ditanyakan, jangan ragu untuk bertanya. 😊"""
        return message

