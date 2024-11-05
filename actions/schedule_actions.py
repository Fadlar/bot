# import requests
# import logging

# from rasa_sdk.events import SlotSet, FollowupAction
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
# from typing import Any, Text, Dict, List
# from fuzzywuzzy import process
# from datetime import datetime

# API_URL = "http://localhost:8001/api/rasa-chatbot" 

# # Inisialisasi logging
# logging.basicConfig(level=logging.INFO)

# class ActionProvideServiceSchedule(Action):
#     def name(self) -> Text:
#         return "action_provide_service_schedule"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#       service_name = tracker.get_slot('service')

#       # membuat panggilan API ke laravel
#       url = f"{API_URL}/services"
#       try:
#          response = requests.get(url)
#          all_services = response.json() # mengambil semua layanan

#          if response.status_code == 200:
#             # mengambil nama layanan dari response
#             service_names = [service['name'] for service in all_services]

#             # menggunakan fuzzy wuzzy untuk mencocokan layanan
#             matched_service, score = process.extractOne(service_name, service_names)
#             if score >= 90:
#               # kecocokan sempurna ditemukan teruskan ke step selanjutnya
#               return [SlotSet('matched_service', matched_service), FollowupAction('action_provide_schedule_info')]
#             # kecocokan sebagian ditemukan, minta konfirmasi
#             elif score >= 70:
#               # mengonfirmasi dengan pengguna
#               confirmation_message = f"Apakah Anda merujuk pada layanan {matched_service}? Mohon konfirmasi agar saya dapat memberikan informasi yang tepat."
#               dispatcher.utter_message(text=confirmation_message)

#               # simpan layanan yang cocok dalam slot untuk langkah selanjutnya
#               return [SlotSet('matched_service', matched_service), FollowupAction('action_provide_schedule_info')]

#             else:
#                message = f"Tidak ada layanan yang cocok ditemukan untuk '{service_name}'. Apakah anda ingin mencoba layanan lain?"

#          else:
#           message = "Tidak ada informasi layanan yang dapat diambil."

#       except Exception as e:
#         logging.error(f"Error saat menghubungi semua layanan: {e}")
#         message = "Maaf, terjadi kesalahan saat menghubungi layanan. Silahkan coba lagi nanti."

#       dispatcher.utter_message(text=message)
#       return []

# class ActionProvideScheduleInfo(Action):
#     def name(self) -> Text:
#         return "action_provide_schedule_info"
   
#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         # daftar hari yang tersedia
#         options = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]

#         # mendapatkan input dari slot
#         matched_service = tracker.get_slot('matched_service')
#         schedule_day = tracker.get_slot('schedule_day')

#         # mapping hari ke properti service
#         day_mapping = {
#             "senin": ("monday_start", "monday_end"),
#             "selasa": ("tuesday_start", "tuesday_end"),
#             "rabu": ("wednesday_start", "wednesday_end"),
#             "kamis": ("thursday_start", "thursday_end"),
#             "jumat": ("friday_start", "friday_end"),
#             "sabtu": ("saturday_start", "saturday_end"),
#             "minggu": ("sunday_start", "sunday_end"),
#         }

#         # membuat panggilan API ke laravel
#         url = f"{API_URL}/schedules/{matched_service}"

#         try:
#             response = requests.get(url)
#             service = response.json() # mengambil info service

#             if response.status_code == 200:
#                 if schedule_day and matched_service:
#                     schedule_day = schedule_day.lower().strip()
#                     matched_day, score = process.extractOne(schedule_day, options)

#                     if score >= 70 and matched_day in day_mapping:
#                         start_prop, end_prop = day_mapping[matched_day]
#                         start_time = service.get(start_prop)
#                         end_time = service.get(end_prop)
#                         if start_time and end_time:
#                             schedule_info_to_display = f"{start_time} - {end_time}"
#                         else:
#                             schedule_info_to_display = "Sedang tutup/libur."
                        
#                         dispatcher.utter_message(text=f"Jadwal operasional untuk layanan {matched_service} di hari {matched_day.capitalize()}: {schedule_info_to_display}")
#                         return []
#                     else:
#                         # jika hari tidak cocok, tampilkan seluruh jadwal
#                         message = self.construct_full_schedule(service, matched_service)
#                         dispatcher.utter_message(text=message)
#                         return []
#                 elif not schedule_day and matched_service:
#                     # tampilkan seluruh jadwal
#                     message = self.construct_full_schedule(service, matched_service)
#                     dispatcher.utter_message(text=message)
#                     return []
                
#                 elif schedule_day and not matched_service:
#                     message = "Maaf, saya perlu tahu layanan apa yang Anda maksud. Bisakah Anda menyebutkan layanan tersebut agar saya bisa membantu Anda lebih baik?"
#                     dispatcher.utter_message(text=message)
#                     return []

#                 else:
#                     message = "Maaf, saya perlu tahu layanan apa yang Anda maksud. Bisakah Anda menyebutkan layanan tersebut agar saya bisa membantu Anda lebih baik?"
#                     dispatcher.utter_message(text=message)
#                     return []
#             else:
#                 message = "Tidak ada informasi layanan yang dapat diambil."
#                 dispatcher.utter_message(text=message)
#                 return []
#         except Exception as e:
#             logging.error(f"Error saat menghubungi layanan: {e}")
#             message = "Maaf, terjadi kesalahan saat menghubungi layanan."
#             dispatcher.utter_message(text=message)
#             return []
        
#     def construct_full_schedule(self, service: Dict, matched_service: Text) -> Text:
#         day_mapping = {
#                 "senin": ("monday_start", "monday_end"),
#                 "selasa": ("tuesday_start", "tuesday_end"),
#                 "rabu": ("wednesday_start", "wednesday_end"),
#                 "kamis": ("thursday_start", "thursday_end"),
#                 "jumat": ("friday_start", "friday_end"),
#                 "sabtu": ("saturday_start", "saturday_end"),
#                 "minggu": ("sunday_start", "sunday_end")
#             }
        
#         schedule_lines = []
#         for day, (start_prop, end_prop) in day_mapping.items():
#             start_time = service.get(start_prop)
#             end_time = service.get(end_prop)
#             if start_time and end_time:
#                 schedule = f"{start_time} - {end_time}"
#             else:
#                 schedule = "Sedang tutup/libur."
#             schedule_lines.append(f"- {day.capitalize()}: {schedule}")

#         message = f"""Berikut jadwal operasional layanan {matched_service}:
#         {chr(10).join(schedule_lines)}
        
#         Semoga informasi ini membantu! Jika ada hal lain yang ingin ditanyakan, jangan ragu untuk bertanya.😊"""
#         return message