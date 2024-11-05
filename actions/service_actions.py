# import requests
# import logging

# from rasa_sdk.events import SlotSet, FollowupAction
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
# from typing import Any, Text, Dict, List
# from fuzzywuzzy import process

# API_URL = "http://localhost:8001/api/rasa-chatbot" 

# # Inisialisasi logging
# logging.basicConfig(level=logging.INFO)

# class ActionProvideService(Action):
#     def name(self) -> Text:
#         return "action_provide_service"

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
#             # service_names_with_abbr = service_names + [name for name in service_names for abbr in service['abbreviations']]

#             # menggunakan fuzzy wuzzy untuk mencocokan layanan
#             matched_service, score = process.extractOne(service_name, service_names)
#             if score >= 90:
#               # kecocokan sempurna ditemukan teruskan ke step selanjutnya
#               return [SlotSet('matched_service', matched_service), FollowupAction('utter_service_info_option')]
#             # kecocokan sebagian ditemukan, minta konfirmasi
#             elif score >= 70:
#               # mengonfirmasi dengan pengguna
#               confirmation_message = f"Apakah Anda merujuk pada layanan {matched_service}? Mohon konfirmasi agar saya dapat memberikan informasi yang tepat."
#               dispatcher.utter_message(text=confirmation_message)

#               # simpan layanan yang cocok dalam slot untuk langkah selanjutnya
#               return [SlotSet('matched_service', matched_service)]

#             else:
#                message = f"Tidak ada layanan yang cocok ditemukan untuk '{service_name}'. Apakah anda ingin mencoba layanan lain?"

#          else:
#           message = "Tidak ada informasi layanan yang dapat diambil."

#       except Exception as e:
#         logging.error(f"Error saat menghubungi semua layanan: {e}")
#         message = "Maaf, terjadi kesalahan saat menghubungi layanan. Silahkan coba lagi nanti."

#       dispatcher.utter_message(text=message)
#       return []
    
# class ActionProvideServiceInfo(Action):
#    def name(self) -> Text:
#       return "action_provide_service_info"
   
#    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#       # daftar opsi yang tersedia
#       options = ["deskripsi", "persyaratan", "mekanisme prosedur", "jangka waktu", "biaya"]

#       # mendapatkan input dari slot
#       matched_service = tracker.get_slot('matched_service')
#       service_info_option = tracker.get_slot('service_info_option')

#       if matched_service is not None and service_info_option is not None:
#          # ambil data dari api
#          url = f"{API_URL}/services/{matched_service}"
#          service_info_option = service_info_option.lower().strip()

#          try:
#             response = requests.get(url)
#             service = response.json() # mengambil info service
          
#             if response.status_code == 200:
#               # menggunakan fuzzy wuzzy untuk mencocokan service yang dipilih oleh user
#               matched_option, score = process.extractOne(service_info_option, options)
#               # menentukan ambang batas 
#               if score >= 70:
#                 if matched_option == "deskripsi":
#                     info_to_display = service.get('description')
#                     if info_to_display is None or info_to_display.strip() == "":
#                         info_to_display = f"Deskripsi untuk {matched_service} tidak tersedia."
#                 elif matched_option == "persyaratan":
#                     info_to_display = service.get('requirements')
#                     if info_to_display is None or info_to_display.strip() == "":
#                         info_to_display = f"Persyaratan untuk {matched_service} tidak tersedia."
#                 elif matched_option == "mekanisme":
#                     info_to_display = service.get('procedure')
#                     if info_to_display is None or info_to_display.strip() == "":
#                         info_to_display = f"Mekanisme & prosedur untuk {matched_service} tidak tersedia."
#                 elif matched_option == "jangka waktu":
#                     info_to_display = service.get('time_period')
#                     if info_to_display is None or info_to_display.strip() == "":
#                         info_to_display = f"Jangka waktu penyelesaian untuk {matched_service} tidak tersedia."
#                 elif matched_option == "biaya":
#                     info_to_display = service.get('tariff')
#                     if info_to_display is None or info_to_display.strip() == "":
#                         info_to_display = f"Biaya atau tarif untuk {matched_service} tidak tersedia."
#                 else:
#                     info_to_display = "Informasi yang diminta tidak tersedia."

#                 dispatcher.utter_message(text=f"Informasi {matched_option} untuk layanan {matched_service}:\n{info_to_display}")
#                 return [SlotSet('matched_service', matched_service)]
#               else:
#                   dispatcher.utter_message(text=f"Maaf, saya tidak menemukan kecocokan yang memadai untuk '{service_info_option}'. Mohon coba dengan kata lain.")
#             else:
#               message = "Tidak ada informasi layanan yang dapat diambil."

#          except Exception as e:
#             logging.error(f"Error saat menghubungi layanan: {e}")
#             message = "Maaf, terjadi kesalahan saat menghubungi layanan. Silahkan coba lagi nanti."
#             dispatcher.utter_message(text=message)
#             return []

# class ActionProvideServiceDirect(Action):
#    def name(self) -> Text:
#       return "action_provide_service_direct"
   
#    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#       # Mendapatkan input layanan dan opsi dari slot
#       service_name = tracker.get_slot('service')
#       service_info_option = tracker.get_slot('service_info_option')

#       if not service_name or not service_info_option:
#           dispatcher.utter_message(text="Maaf, saya memerlukan nama layanan dan opsi informasi yang jelas. Silakan sebutkan kembali.")
#           return []

#       # Panggilan API untuk mendapatkan semua layanan
#       try:
#           url = f"{API_URL}/services"
#           response = requests.get(url)
#           all_services = response.json()

#           if response.status_code == 200:
#               # Mengambil nama layanan dari response
#               service_names = [service['name'] for service in all_services]

#               # Menggunakan fuzzywuzzy untuk mencocokkan layanan
#               matched_service, score = process.extractOne(service_name, service_names)
#               if matched_service is not None:
#                 if score >= 70:
#                     # Jika layanan ditemukan, ambil detail layanan dari API
#                     url_service_detail = f"{API_URL}/services/{matched_service}"
#                     response_detail = requests.get(url_service_detail)
#                     service_detail = response_detail.json()

#                     if response_detail.status_code == 200:
#                         # Daftar opsi informasi yang tersedia
#                         options = ["deskripsi", "persyaratan", "mekanisme prosedur", "jangka waktu", "biaya"]

#                         # Menggunakan fuzzywuzzy untuk mencocokkan opsi informasi
#                         matched_option, option_score = process.extractOne(service_info_option.lower().strip(), options)
#                         if option_score >= 70:
#                             # Menampilkan informasi berdasarkan opsi yang dipilih
#                             if matched_option == "deskripsi":
#                                 info_to_display = service_detail.get('description')
#                                 if info_to_display is None or info_to_display.strip() == "":
#                                     info_to_display = f"Deskripsi untuk {matched_service} tidak tersedia."
#                             elif matched_option == "persyaratan":
#                                 info_to_display = service_detail.get('requirements')
#                                 if info_to_display is None or info_to_display.strip() == "":
#                                     info_to_display = f"Persyaratan untuk {matched_service} tidak tersedia."
#                             elif matched_option == "mekanisme":
#                                 info_to_display = service_detail.get('procedure')
#                                 if info_to_display is None or info_to_display.strip() == "":
#                                     info_to_display = f"Mekanisme & prosedur untuk {matched_service} tidak tersedia."
#                             elif matched_option == "jangka waktu":
#                                 info_to_display = service_detail.get('time_period')
#                                 if info_to_display is None or info_to_display.strip() == "":
#                                     info_to_display = f"Jangka waktu penyelesaian untuk {matched_service} tidak tersedia."
#                             elif matched_option == "biaya":
#                                 info_to_display = service_detail.get('tariff')
#                                 if info_to_display is None or info_to_display.strip() == "":
#                                     info_to_display = f"Biaya atau tarif untuk {matched_service} tidak tersedia."
#                             else:
#                                 info_to_display = "Informasi yang diminta tidak tersedia."


#                             dispatcher.utter_message(text=f"Informasi {matched_option} untuk layanan {matched_service}:\n{info_to_display}")
#                             return [SlotSet('matched_service', matched_service)]

#                         else:
#                             dispatcher.utter_message(text=f"Maaf, saya tidak menemukan kecocokan yang memadai untuk '{service_info_option}'. Mohon coba dengan kata lain.")
#                             return [SlotSet('matched_service', matched_service)]
#                     else:
#                         dispatcher.utter_message(text="Maaf, terjadi kesalahan saat mengambil detail layanan.")
#                         return []

#                 else:
#                     dispatcher.utter_message(text=f"Tidak ada layanan yang cocok ditemukan untuk '{service_name}'. Silakan coba layanan lain.")
#                     return []
#               else:
#                     dispatcher.utter_message(text=f"Mohon masukan layanan yang valid.")
#                     return []

#           else:
#               dispatcher.utter_message(text="Maaf, saya tidak mengenali layanan tersebut. Mohon pastikan Anda memasukkan nama layanan yang valid atau silakan coba lagi dengan kata kunci yang berbeda.")
#               return []

#       except Exception as e:
#           logging.error(f"Error saat menghubungi layanan: {e}")
#           dispatcher.utter_message(text="Maaf, terjadi kesalahan saat menghubungi layanan. Silakan coba lagi nanti.")
#           return []


