# -*- coding: utf-8 -*-
"""
Z Kitap Mobile Engine & Server (v2.0)
Mobil Cihazlar (Telefon & Tablet) İçin Yüksek Hızlı Z-Kitap ve Flip İndirme Motoru
- Altın Karne (Soru / Çözüm / Her İkisi)
- Sınav Dijital (Soru / Çözüm / Her İkisi)
- Fernus Web & Fenomen (141 Yayınevi AES-CBC Şifre Çözücü)
- Supara & FlipBook (Jet Motoru)
- FlipHTML5
- Telefonun Tarayıcısına Doğrudan PDF İndirme & Kütüphane Yönetimi
"""

import os, sys, re, json, time, io, uuid, urllib.request, urllib.error, urllib.parse, ssl, threading, shutil, base64
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except Exception:
    HAS_CRYPTO = False

try:
    import img2pdf
except ImportError:
    img2pdf = None

# -*- coding: utf-8 -*-
"""Fernus 141 Yayinevi Gomulu Kripto Veritabani"""

YAYINEVLERI_DATA = {'1': {'numara': '1', 'publisher': 'Murat Yayınları', 'pkxkname': 'muratyayinlari', 'prefix': None, 'fernusCode_sifreli': '==AF/iokYABaQejzEE9eAsba', 'fernusCode_gercek': '6_4_8'}, '10': {'numara': '10', 'publisher': 'Köşebilgi Yayınları', 'pkxkname': 'kosebilgiyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wDaI1/vFy3tJm2FTDRDkF3', 'fernusCode_gercek': '9_11_22'}, '100': {'numara': '100', 'publisher': 'Pat Yayınları', 'pkxkname': 'pat', 'prefix': None, 'fernusCode_sifreli': '==woR1aSAfXYQPaIaoSDYUaI', 'fernusCode_gercek': '10_6_12'}, '102': {'numara': '102', 'publisher': 'Akademik Başarı', 'pkxkname': 'akademikbasari', 'prefix': None, 'fernusCode_sifreli': '==gE3MYl+zoyNbNdGDWFGMC4', 'fernusCode_gercek': '2_26_21'}, '104': {'numara': '104', 'publisher': 'Adım Adım Işıklı', 'pkxkname': 'adimadimisikli', 'prefix': None, 'fernusCode_sifreli': '==g8kC13Omm6xI3SUhriqgaG', 'fernusCode_gercek': '8_13_9'}, '105': {'numara': '105', 'publisher': 'Artı Eğitim', 'pkxkname': 'artiegitim', 'prefix': None, 'fernusCode_sifreli': '==AbkzlcXqtBPAehnrEioLF0', 'fernusCode_gercek': '8_9_18'}, '106': {'numara': '106', 'publisher': 'Sonuc', 'pkxkname': 'sonuc', 'prefix': None, 'fernusCode_sifreli': '==wgBN5yBec3KqZeERJgutah', 'fernusCode_gercek': '5_6_8'}, '11': {'numara': '11', 'publisher': 'Vip Yayınları', 'pkxkname': 'vipyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wJuOwK33z0KIhqyMKpdNOs', 'fernusCode_gercek': '8_2_4'}, '12': {'numara': '12', 'publisher': 'Çanta Yayıncılık', 'pkxkname': 'canta', 'prefix': None, 'fernusCode_sifreli': '==A4udGEOLpcHQyAJr4jYHJb', 'fernusCode_gercek': '2_12_24'}, '14': {'numara': '14', 'publisher': 'Oksijen Yayınları', 'pkxkname': 'oksijen', 'prefix': None, 'fernusCode_sifreli': '==ATEqsLIa7ExwmWmfUYaVQt', 'fernusCode_gercek': '26_10_20'}, '15': {'numara': '15', 'publisher': 'Hiper Zeka', 'pkxkname': 'hiperzeka', 'prefix': None, 'fernusCode_sifreli': '==AYsj8fKLD/KHzNGnvhbxDb', 'fernusCode_gercek': '8_4_8'}, '17': {'numara': '17', 'publisher': 'Kronometre Yayınları', 'pkxkname': 'kronometreyayinlari', 'prefix': None, 'fernusCode_sifreli': '==QPRO59g91NazOxVFhlKjjZ', 'fernusCode_gercek': '16_11_22'}, '19': {'numara': '19', 'publisher': 'Avantaj Yayınları', 'pkxkname': 'avantaj', 'prefix': None, 'fernusCode_sifreli': '==g99Mu8ZT2cdeNjzqBX5RY1', 'fernusCode_gercek': '11_2_4'}, '2': {'numara': '2', 'publisher': 'MUBA', 'pkxkname': 'muba', 'prefix': None, 'fernusCode_sifreli': '==Q2WphUNNMYDWvx8XOFGsYK', 'fernusCode_gercek': '4_7_14'}, '20': {'numara': '20', 'publisher': 'Avantaj Yayınları', 'pkxkname': 'avantaj', 'prefix': None, 'fernusCode_sifreli': '==g99Mu8ZT2cdeNjzqBX5RY1', 'fernusCode_gercek': '11_2_4'}, '206': {'numara': '206', 'publisher': 'Netiz Yayınları', 'pkxkname': 'netiz', 'prefix': None, 'fernusCode_sifreli': '==wQp39KPtGyi2dA/KT/aBCJ', 'fernusCode_gercek': '2_26_19'}, '209': {'numara': '209', 'publisher': 'Toprak Yayıncılık', 'pkxkname': 'toprak', 'prefix': None, 'fernusCode_sifreli': '==A2MJ/AtSuzAjElex9c3Dbt', 'fernusCode_gercek': '9_5_10'}, '21': {'numara': '21', 'publisher': 'Esen Yayınları', 'pkxkname': 'esenyayinlari', 'prefix': None, 'fernusCode_sifreli': '==QAiSmulgqD4cxwaBKNSbZQ', 'fernusCode_gercek': '3_6_10'}, '210': {'numara': '210', 'publisher': 'Dakika Yayınları', 'pkxkname': 'dakikayayinlari', 'prefix': None, 'fernusCode_sifreli': '==wCEoHVslc2hl37TdBoCAlD', 'fernusCode_gercek': '21_4_8'}, '213': {'numara': '213', 'publisher': 'Paragrafın Şifresi', 'pkxkname': 'paragrafinsifresi', 'prefix': None, 'fernusCode_sifreli': '==wA4yRIkLGcJs+p27NkDijb', 'fernusCode_gercek': '6_10_20'}, '216': {'numara': '216', 'publisher': 'Speed Up', 'pkxkname': 'speedup', 'prefix': None, 'fernusCode_sifreli': '==Q+y1orNY+EU1ww2jYjEqdL', 'fernusCode_gercek': '8_11_22'}, '218': {'numara': '218', 'publisher': 'ilkokul1.com Yayınları', 'pkxkname': 'ilkokul1', 'prefix': None, 'fernusCode_sifreli': '==gAOMVMREVNabUZyt7KE7ZB', 'fernusCode_gercek': '17_4_8'}, '223': {'numara': '223', 'publisher': 'Duyu Yayınları', 'pkxkname': 'duyu', 'prefix': None, 'fernusCode_sifreli': '==QBIWXPFWHCM4rV1NeE0Yfn', 'fernusCode_gercek': '2_26_16'}, '224': {'numara': '224', 'publisher': 'Birikim Yayınları', 'pkxkname': 'birikim', 'prefix': None, 'fernusCode_sifreli': '==wopvdaLOxx1SjgjfAIw1aC', 'fernusCode_gercek': '2_26_15'}, '225': {'numara': '225', 'publisher': 'MOTİVASYON', 'pkxkname': 'motivasyon', 'prefix': None, 'fernusCode_sifreli': '==AmZBU/204gYeWYPHRn3Ihq', 'fernusCode_gercek': '25_4_8'}, '226': {'numara': '226', 'publisher': 'Fatih Ay Yayınları', 'pkxkname': 'fatihay', 'prefix': None, 'fernusCode_sifreli': '==gtwHfa74M4jHQACC6OM7up', 'fernusCode_gercek': '2_26_14'}, '229': {'numara': '229', 'publisher': 'Talent Team Yayıncılık', 'pkxkname': 'dijitaltalent', 'prefix': None, 'fernusCode_sifreli': '==wZyK46Be26ahPrMisCWlUd', 'fernusCode_gercek': '2_26_7'}, '23': {'numara': '23', 'publisher': 'Limit', 'pkxkname': 'limit', 'prefix': None, 'fernusCode_sifreli': '==wsE9pwKiWrdIBdOGXPYAOF', 'fernusCode_gercek': '4_17_5'}, '230': {'numara': '230', 'publisher': 'Yunus Emre Yayınları', 'pkxkname': 'yunusemre', 'prefix': None, 'fernusCode_sifreli': '==Qam6cbV1/z0AzpA3ekXrJa', 'fernusCode_gercek': '2_26_6'}, '24': {'numara': '24', 'publisher': 'Limit', 'pkxkname': 'limit', 'prefix': None, 'fernusCode_sifreli': '==wsE9pwKiWrdIBdOGXPYAOF', 'fernusCode_gercek': '4_17_5'}, '25': {'numara': '25', 'publisher': 'More And More', 'pkxkname': 'kurmay', 'prefix': None, 'fernusCode_sifreli': '==AnR1upKjObnIRg9TCHJzNP', 'fernusCode_gercek': '1_4_8'}, '293': {'numara': '293', 'publisher': 'Öncelik Yayınları', 'pkxkname': 'oncelikyayinlari', 'prefix': None, 'fernusCode_sifreli': '==AQgR6/Jtzt6Pe0NhzEb2CP', 'fernusCode_gercek': '16_1_2'}, '30': {'numara': '30', 'publisher': 'Hız Yayınları', 'pkxkname': 'hizyayinlari', 'prefix': None, 'fernusCode_sifreli': '==gNBvPrdq9uAUPH7mA4sbIu', 'fernusCode_gercek': '3_3_6'}, '31': {'numara': '31', 'publisher': 'NFT Yayınları', 'pkxkname': 'nftyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wU6JnbbSPHMdOQDQ5DvI+z', 'fernusCode_gercek': '26_5_10'}, '32': {'numara': '32', 'publisher': 'Günay Yayınları', 'pkxkname': 'gunayyayinlari', 'prefix': None, 'fernusCode_sifreli': '==AMc23nfN/+IG9rJbDB7guP', 'fernusCode_gercek': '9_4_8'}, '33': {'numara': '33', 'publisher': 'Gizli Yayınları', 'pkxkname': 'gizliyayinlari', 'prefix': None, 'fernusCode_sifreli': '==AvFWBhpk8c3rrTZcUhGlbE', 'fernusCode_gercek': '1_21_6'}, '34': {'numara': '34', 'publisher': 'Yanıt Yayınları', 'pkxkname': 'yanityayinlari', 'prefix': None, 'fernusCode_sifreli': '==gL4Oqdl4F83TSqVDTGkSaQ', 'fernusCode_gercek': '9_12_24'}, '35': {'numara': '35', 'publisher': 'Üçgen', 'pkxkname': 'ucgen', 'prefix': None, 'fernusCode_sifreli': '==AjXosd8tzz6kb3eiuTBNu6', 'fernusCode_gercek': '17_18_20'}, '355': {'numara': '355', 'publisher': 'EĞİTİM DEPOSU YAYINLARI', 'pkxkname': 'egitimdeposu', 'prefix': None, 'fernusCode_sifreli': '==giYAdO0wGvERRD6FCMMzmz', 'fernusCode_gercek': '2_26_4'}, '356': {'numara': '356', 'publisher': 'Madalyon Yayıncılık', 'pkxkname': 'madalyon', 'prefix': None, 'fernusCode_sifreli': '==gwhBondhHp7jKsAJetHL4C', 'fernusCode_gercek': '12_9_18'}, '357': {'numara': '357', 'publisher': 'BalKüpü Yayınları', 'pkxkname': 'balkupu', 'prefix': None, 'fernusCode_sifreli': '==AkQybIFj/rwosYBKDrQnfy', 'fernusCode_gercek': '2_26_5'}, '358': {'numara': '358', 'publisher': 'Deniz Pınar Yayıncılık', 'pkxkname': 'denizpinar', 'prefix': None, 'fernusCode_sifreli': '==QA9iXSUOV4f4XsknAzukym', 'fernusCode_gercek': '2_26_2'}, '359': {'numara': '359', 'publisher': 'Paraf Akademi', 'pkxkname': 'parafakademi', 'prefix': None, 'fernusCode_sifreli': '==AubnAL6wdElsI3lmw5X83G', 'fernusCode_gercek': '2_26_3'}, '360': {'numara': '360', 'publisher': 'Artıbir Yayınları', 'pkxkname': 'artibir', 'prefix': None, 'fernusCode_sifreli': '==AGWMtIPpSXzvFnU5UFn2y+', 'fernusCode_gercek': '5_4_8'}, '362': {'numara': '362', 'publisher': 'Bilnet Okulları', 'pkxkname': 'bilnet', 'prefix': None, 'fernusCode_sifreli': '==AO7tx0l2ncIUDnJFsaLbiM', 'fernusCode_gercek': '1_1_26'}, '363': {'numara': '363', 'publisher': 'ProFizik Yayınları', 'pkxkname': 'profizik', 'prefix': None, 'fernusCode_sifreli': '==QZGl48QvQUDf5zGjb08K1n', 'fernusCode_gercek': '2_24_26'}, '364': {'numara': '364', 'publisher': 'z-Kitap Dijital', 'pkxkname': 'zkitapdijital', 'prefix': None, 'fernusCode_sifreli': '==Qh2DPyazTd6gWM2ClWCBBK', 'fernusCode_gercek': '2_24_25'}, '366': {'numara': '366', 'publisher': 'Format Yayınları', 'pkxkname': 'formatyayinlari', 'prefix': None, 'fernusCode_sifreli': '==w3fQ6vHmMe9dOuIHC8+KqA', 'fernusCode_gercek': '2_24_23'}, '367': {'numara': '367', 'publisher': 'Probil', 'pkxkname': 'probilzkitap', 'prefix': None, 'fernusCode_sifreli': '==g8DpZutt6vJ564VeX5OLBn', 'fernusCode_gercek': '2_24_22'}, '368': {'numara': '368', 'publisher': 'Voltaj Okul', 'pkxkname': 'voltajokul', 'prefix': None, 'fernusCode_sifreli': '==wxEz2FadyZos/+AV2llcEQ', 'fernusCode_gercek': '2_24_21'}, '369': {'numara': '369', 'publisher': 'Bilimetik Yayınları', 'pkxkname': 'bilimetrik', 'prefix': None, 'fernusCode_sifreli': '==QJBDHhPPoJWncsP4aZKr9Z', 'fernusCode_gercek': '24_8_16'}, '37': {'numara': '37', 'publisher': 'PRF Yayınları', 'pkxkname': 'prfyayinlari', 'prefix': None, 'fernusCode_sifreli': '==A/S54mXutxHJLGBso1CazI', 'fernusCode_gercek': '8_1_2'}, '370': {'numara': '370', 'publisher': 'Fernus Yayınları', 'pkxkname': 'fernus', 'prefix': None, 'fernusCode_sifreli': '==wxEz2FadyZos/+AV2llcEQ', 'fernusCode_gercek': '2_24_21'}, '371': {'numara': '371', 'publisher': 'Fen Bilimleri', 'pkxkname': 'fenbilimleri', 'prefix': None, 'fernusCode_sifreli': '==gcFrbusvjZPJmSovWfho3K', 'fernusCode_gercek': '8_16_24'}, '372': {'numara': '372', 'publisher': 'XRAY Yayınları', 'pkxkname': 'xray', 'prefix': None, 'fernusCode_sifreli': '==wgPIL31kY6+mXWyDg2h3qd', 'fernusCode_gercek': '2_24_20'}, '373': {'numara': '373', 'publisher': 'FİLBAZ ÇOCUK YAYINCILIK', 'pkxkname': 'filbazcocuk', 'prefix': None, 'fernusCode_sifreli': '==Q5GF4wMjqLRY+DEBZMhtsl', 'fernusCode_gercek': '2_26_17'}, '374': {'numara': '374', 'publisher': 'İksir Yayıncılık', 'pkxkname': 'iksir', 'prefix': None, 'fernusCode_sifreli': '==gG0KIWisvjWUKmzOWOAaKL', 'fernusCode_gercek': '2_24_19'}, '375': {'numara': '375', 'publisher': 'Elfi Yayıncılık', 'pkxkname': 'elfi', 'prefix': None, 'fernusCode_sifreli': '==Af74XUOaaFvaX13Fshmvmv', 'fernusCode_gercek': '2_24_18'}, '376': {'numara': '376', 'publisher': 'Schola', 'pkxkname': 'schola', 'prefix': None, 'fernusCode_sifreli': '==AdBia3LvUrUzAD49qmNKvF', 'fernusCode_gercek': '19_13_26'}, '387': {'numara': '387', 'publisher': 'İsem Yayıncılık', 'pkxkname': 'dijitalisem', 'prefix': None, 'fernusCode_sifreli': '==wU/j8lFU//VUS9ahDjpZHd', 'fernusCode_gercek': '2_24_15'}, '39': {'numara': '39', 'publisher': 'Ankara Yayıncılık', 'pkxkname': 'ankarayayincilik', 'prefix': None, 'fernusCode_sifreli': '==gbL8TeNxdRLsv3Io/Tiafz', 'fernusCode_gercek': '6_13_26'}, '390': {'numara': '390', 'publisher': 'Arena Yayınları', 'pkxkname': 'arena', 'prefix': None, 'fernusCode_sifreli': '==AaOq0ukPh9ByDKPwY6VdbA', 'fernusCode_gercek': '2_24_13'}, '391': {'numara': '391', 'publisher': 'Forvet Yayınları', 'pkxkname': 'forvet', 'prefix': None, 'fernusCode_sifreli': '==wXw9LGqCYMEn0/xbzwrMly', 'fernusCode_gercek': '2_24_12'}, '392': {'numara': '392', 'publisher': 'Narataş Yayınları', 'pkxkname': 'naratas', 'prefix': None, 'fernusCode_sifreli': '==QQl2dMTxz1rPqRPNwhkE+m', 'fernusCode_gercek': '2_24_11'}, '4': {'numara': '4', 'publisher': 'ASPIRING PUBLISHING', 'pkxkname': 'aspiring', 'prefix': None, 'fernusCode_sifreli': '==QNNU4q2cHQ8y7K7gSocL+H', 'fernusCode_gercek': '2_1_15'}, '402': {'numara': '402', 'publisher': 'Mobese Yayınları', 'pkxkname': 'mobese', 'prefix': None, 'fernusCode_sifreli': '==AapBnSIsjMMZ8wcE5UlnKd', 'fernusCode_gercek': '2_24_10'}, '41': {'numara': '41', 'publisher': 'Karekök Yayınları', 'pkxkname': 'karekokyayinlari', 'prefix': None, 'fernusCode_sifreli': '==gVeGkJ0/8YgLGYSWsLjDa8', 'fernusCode_gercek': '6_2_4'}, '42': {'numara': '42', 'publisher': 'X Yayıncılık', 'pkxkname': 'xyayincilik', 'prefix': None, 'fernusCode_sifreli': '==A96rLMRuGSC/rtsHB4XsEl', 'fernusCode_gercek': '2_1_3'}, '43': {'numara': '43', 'publisher': 'Ünlüler Karması', 'pkxkname': 'unlulerkarmasi', 'prefix': None, 'fernusCode_sifreli': '==QRPK1fVFC7Ep6W7xG7a92J', 'fernusCode_gercek': '26_12_24'}, '45': {'numara': '45', 'publisher': 'ÜçDörtBeş Yayınları', 'pkxkname': 'ucdortbesyayinlari', 'prefix': None, 'fernusCode_sifreli': '==gxwddJKhIykBKkOQIId+pb', 'fernusCode_gercek': '1_10_20'}, '46': {'numara': '46', 'publisher': 'ATA', 'pkxkname': 'ata', 'prefix': None, 'fernusCode_sifreli': '==An8RxfOotF89x7TeOr/9W/', 'fernusCode_gercek': '1_2_6'}, '48': {'numara': '48', 'publisher': 'ERADİL', 'pkxkname': 'eradil', 'prefix': None, 'fernusCode_sifreli': '==A5txWzLP3fPC++lB5rzW6Z', 'fernusCode_gercek': '26_3_6'}, '49': {'numara': '49', 'publisher': 'ÖRNEK AKADEMİ', 'pkxkname': 'ornekakademi', 'prefix': None, 'fernusCode_sifreli': '==QgRlkkRiXNSfzJz4PznBzu', 'fernusCode_gercek': '10_3_6'}, '5': {'numara': '5', 'publisher': 'ADAY YAYINLARI', 'pkxkname': 'adayyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wC8O67p2rwJa5pg7Jmqq1V', 'fernusCode_gercek': '26_2_4'}, '52': {'numara': '52', 'publisher': 'Rasyonel Yayınları', 'pkxkname': 'rasyonelyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wxWtljSPBY0FAstVYHeT6H', 'fernusCode_gercek': '21_13_26'}, '53': {'numara': '53', 'publisher': 'Fi Yayınları', 'pkxkname': 'fiyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wxzA+Rb9WWooWcxb5V0Vwe', 'fernusCode_gercek': '7_3_6'}, '54': {'numara': '54', 'publisher': 'Tammat', 'pkxkname': 'tammat', 'prefix': None, 'fernusCode_sifreli': '==AXruj34HL+qS3wplDY5sJ2', 'fernusCode_gercek': '1_1_2'}, '55': {'numara': '55', 'publisher': 'Kaliteli Eğitim Yayınları', 'pkxkname': 'keyyayinlari', 'prefix': None, 'fernusCode_sifreli': '==gTzqZhwkeeM/2y4chgH59K', 'fernusCode_gercek': '22_12_24'}, '56': {'numara': '56', 'publisher': 'EKSPERT', 'pkxkname': 'ekspert', 'prefix': None, 'fernusCode_sifreli': '==AqG7FYF10BzZvXQilZKvwV', 'fernusCode_gercek': '17_2_4'}, '57': {'numara': '57', 'publisher': 'Optik Yayinlari', 'pkxkname': 'optikyayinlari', 'prefix': None, 'fernusCode_sifreli': '==QasKfygqWno03fBC1xRCJ6', 'fernusCode_gercek': '2_1_19'}, '58': {'numara': '58', 'publisher': 'Model Eğitim', 'pkxkname': 'modelegitim', 'prefix': None, 'fernusCode_sifreli': '==Azq7kXSfbLPgITSUt0QhH0', 'fernusCode_gercek': '7_14_22'}, '59': {'numara': '59', 'publisher': 'Endemik Yayınları', 'pkxkname': 'endemikyayinlari', 'prefix': None, 'fernusCode_sifreli': '==Qng9TFFFHPB4P36t8gYjBS', 'fernusCode_gercek': '22_1_2'}, '6': {'numara': '6', 'publisher': 'IQ YAYINLARI', 'pkxkname': 'iqyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wzAl/mqt0tG7Uz6KCklYN0', 'fernusCode_gercek': '2_1_5'}, '60': {'numara': '60', 'publisher': 'Meraklı Zihinler', 'pkxkname': 'meraklizihinler', 'prefix': None, 'fernusCode_sifreli': '==g6Vd3CMgTUqeysyQpTf3xN', 'fernusCode_gercek': '1_11_16'}, '62': {'numara': '62', 'publisher': 'Kültür Yayıncılık', 'pkxkname': 'dijiogretmen', 'prefix': None, 'fernusCode_sifreli': '==QJivUYSNn30COKDZF8XvRx', 'fernusCode_gercek': '9_10_12'}, '63': {'numara': '63', 'publisher': 'Benim Hocam', 'pkxkname': 'benimhocam', 'prefix': None, 'fernusCode_sifreli': '==AkCKme1wgqxQvzlnlTFHG+', 'fernusCode_gercek': '23_11_22'}, '65': {'numara': '65', 'publisher': 'Mavi Tikli Yayıncılık', 'pkxkname': 'mavitikli', 'prefix': None, 'fernusCode_sifreli': '==wWWv+obntg8cN0zES+KQSX', 'fernusCode_gercek': '25_7_14'}, '66': {'numara': '66', 'publisher': 'Altın Karma Yayınları', 'pkxkname': 'altinkarma', 'prefix': None, 'fernusCode_sifreli': '==QQEgQmMSJrk5Y84mrFcMFP', 'fernusCode_gercek': '23_10_20'}, '67': {'numara': '67', 'publisher': 'Startfen', 'pkxkname': 'startfen', 'prefix': None, 'fernusCode_sifreli': '==AaQCpHM5UwBpD66DuVO2lv', 'fernusCode_gercek': '1_12_15'}, '68': {'numara': '68', 'publisher': 'Çalışkan Arı', 'pkxkname': 'caliskanari', 'prefix': None, 'fernusCode_sifreli': '==AzUjEdd2E/qMO3Ni/Fac52', 'fernusCode_gercek': '6_15_7'}, '69': {'numara': '69', 'publisher': 'FOR EN ELT', 'pkxkname': 'forenelt', 'prefix': None, 'fernusCode_sifreli': '==gWU5JGkBjgn7gK7bI6nKjw', 'fernusCode_gercek': '26_9_18'}, '7': {'numara': '7', 'publisher': 'Strateji Yayınları', 'pkxkname': 'stratejiyayinlari', 'prefix': None, 'fernusCode_sifreli': '==Q8QOYP8lqrMjlI04N52sj+', 'fernusCode_gercek': '19_2_4'}, '70': {'numara': '70', 'publisher': 'Zeka Küpü Yayınları', 'pkxkname': 'zekakupuyayinlari', 'prefix': None, 'fernusCode_sifreli': '==wI0yqxo/JixmCNrgLixFRu', 'fernusCode_gercek': '9_10_20'}, '78': {'numara': '78', 'publisher': 'Tekden', 'pkxkname': 'tekden', 'prefix': None, 'fernusCode_sifreli': '==QM6z4zjboczMHUw7aGlsXh', 'fernusCode_gercek': '2_17_1'}, '81': {'numara': '81', 'publisher': 'Data Yayınları', 'pkxkname': 'data', 'prefix': None, 'fernusCode_sifreli': '==QDUkVsFQ44oOeglWUBYPky', 'fernusCode_gercek': '2_17_4'}, '82': {'numara': '82', 'publisher': 'Analiz Yayınları', 'pkxkname': 'analiz', 'prefix': None, 'fernusCode_sifreli': '==Q482czemjUSMDX0rKoO7Ug', 'fernusCode_gercek': '7_8_10'}, '83': {'numara': '83', 'publisher': 'GO Yayınları', 'pkxkname': 'goyayinlari', 'prefix': None, 'fernusCode_sifreli': '==w3URlqN9PxSD2fd5Hdq4rc', 'fernusCode_gercek': '22_6_12'}, '84': {'numara': '84', 'publisher': 'Berkay Yayıncılık', 'pkxkname': 'berkay', 'prefix': None, 'fernusCode_sifreli': '==QbFxNernnvrPf06wqcaR7t', 'fernusCode_gercek': '26_7_14'}, '86': {'numara': '86', 'publisher': 'Mozaik Yayınları', 'pkxkname': 'mozaikyayinlari', 'prefix': None, 'fernusCode_sifreli': '==QSfM1nwZRaRqgLYvi0sjPr', 'fernusCode_gercek': '23_12_24'}, '87': {'numara': '87', 'publisher': 'Yükseliş Dijital', 'pkxkname': 'yukselis', 'prefix': None, 'fernusCode_sifreli': '==gMus4aTt2EcjN32+tpVcby', 'fernusCode_gercek': '2_26_25'}, '88': {'numara': '88', 'publisher': 'Ordinat Yayınlari', 'pkxkname': 'ordinatyayinlari', 'prefix': None, 'fernusCode_sifreli': '==QFg2cBBrQhhuUH5JatbI9s', 'fernusCode_gercek': '26_8_16'}, '89': {'numara': '89', 'publisher': 'Karacan Eğitim Kurumları', 'pkxkname': 'karacan', 'prefix': None, 'fernusCode_sifreli': '==AqXpk5lh+ZpAx/5vRvA3lw', 'fernusCode_gercek': '2_1_17'}, '9': {'numara': '9', 'publisher': 'Adrenalin Yayınları', 'pkxkname': 'adrenalin', 'prefix': None, 'fernusCode_sifreli': '==ABTmZ0A3VaRNQyN1tbuXbP', 'fernusCode_gercek': '26_6_12'}, '92': {'numara': '92', 'publisher': 'Kondisyon Dijital', 'pkxkname': 'kondisyon', 'prefix': None, 'fernusCode_sifreli': '==AyGzr5c6aE7ZUGapGQXeoj', 'fernusCode_gercek': '2_26_22'}, '93': {'numara': '93', 'publisher': 'Koşul Yayıncılık', 'pkxkname': 'kosulyayincilik', 'prefix': None, 'fernusCode_sifreli': '==AO7tx0l2ncIUDnJFsaLbiM', 'fernusCode_gercek': '1_1_26'}, '95': {'numara': '95', 'publisher': 'Açı Yayınları', 'pkxkname': 'aciyayinlari', 'prefix': None, 'fernusCode_sifreli': '==QI69uD1036wrzP4+sHLZzg', 'fernusCode_gercek': '21_11_22'}, '96': {'numara': '96', 'publisher': 'Pruva Akademi', 'pkxkname': 'pruvaakademi', 'prefix': None, 'fernusCode_sifreli': '==wmJzlWu7X6MNVzeztmUF9W', 'fernusCode_gercek': '18_6_12'}, '97': {'numara': '97', 'publisher': 'Matsev Yayıncılık', 'pkxkname': 'matsevyayincilik', 'prefix': None, 'fernusCode_sifreli': '==AbGIVwSI82DDHwaO6AZxu0', 'fernusCode_gercek': '19_10_20'}, '98': {'numara': '98', 'publisher': 'TED', 'pkxkname': 'ted', 'prefix': None, 'fernusCode_sifreli': '==QgMbLHgc08ZvK5gFfuPZfY', 'fernusCode_gercek': '24_3_6'}, 'altinkarma': {'numara': 'altinkarma', 'publisher': 'Altın Karma Yayınları', 'pkxkname': 'altinkarma', 'prefix': 'altinkarma', 'fernusCode_sifreli': '==QQEgQmMSJrk5Y84mrFcMFP', 'fernusCode_gercek': '23_10_20'}, 'analiz': {'numara': 'analiz', 'publisher': 'Analiz Yayınları', 'pkxkname': 'analiz', 'prefix': 'analiz', 'fernusCode_sifreli': '==Q482czemjUSMDX0rKoO7Ug', 'fernusCode_gercek': '7_8_10'}, 'ankarayayincilik': {'numara': 'ankarayayincilik', 'publisher': 'Ankara Yayıncılık', 'pkxkname': 'ankarayayincilik', 'prefix': 'ankarayayincilik', 'fernusCode_sifreli': '==gbL8TeNxdRLsv3Io/Tiafz', 'fernusCode_gercek': '6_13_26'}, 'ari': {'numara': 'ari', 'publisher': 'Arı', 'pkxkname': 'ari', 'prefix': 'ari', 'fernusCode_sifreli': '==wgwv4nLemBsshAOG+fYpVS', 'fernusCode_gercek': '7_14_21'}, 'artibir': {'numara': 'artibir', 'publisher': 'Artıbir Yayınları', 'pkxkname': 'artibir', 'prefix': 'artibir', 'fernusCode_sifreli': '==AGWMtIPpSXzvFnU5UFn2y+', 'fernusCode_gercek': '5_4_8'}, 'ata': {'numara': 'ata', 'publisher': 'ATA', 'pkxkname': 'ata', 'prefix': 'ata', 'fernusCode_sifreli': '==An8RxfOotF89x7TeOr/9W/', 'fernusCode_gercek': '1_2_6'}, 'benimhocam': {'numara': 'benimhocam', 'publisher': 'Benim Hocam', 'pkxkname': 'benimhocam', 'prefix': 'benimhocam', 'fernusCode_sifreli': '==AkCKme1wgqxQvzlnlTFHG+', 'fernusCode_gercek': '23_11_22'}, 'bilfen': {'numara': 'bilfen', 'publisher': 'Bilfen', 'pkxkname': 'bilfen', 'prefix': 'bilfen', 'fernusCode_sifreli': '==gJDjWtDlljMO/RjggifEPV', 'fernusCode_gercek': '3_12_24'}, 'caliskanari': {'numara': 'caliskanari', 'publisher': 'Çalışkan Arı', 'pkxkname': 'caliskanari', 'prefix': 'caliskanari', 'fernusCode_sifreli': '==AzUjEdd2E/qMO3Ni/Fac52', 'fernusCode_gercek': '6_15_7'}, 'canta': {'numara': 'canta', 'publisher': 'Çanta Yayıncılık', 'pkxkname': 'canta', 'prefix': 'canta', 'fernusCode_sifreli': '==A4udGEOLpcHQyAJr4jYHJb', 'fernusCode_gercek': '2_12_24'}, 'dereceyayinlari': {'numara': 'dereceyayinlari', 'publisher': 'Derece Yayınları', 'pkxkname': 'dereceyayinlari', 'prefix': 'dereceyayinlari', 'fernusCode_sifreli': '==gTLk4vh6wNZcH4VPbNneiW', 'fernusCode_gercek': '6_7_9'}, 'endemikyayinlari': {'numara': 'endemikyayinlari', 'publisher': 'Endemik Yayınları', 'pkxkname': 'endemikyayinlari', 'prefix': 'endemikyayinlari', 'fernusCode_sifreli': '==Qng9TFFFHPB4P36t8gYjBS', 'fernusCode_gercek': '22_1_2'}, 'esenyayinlari': {'numara': 'esenyayinlari', 'publisher': 'Esen Yayınları', 'pkxkname': 'esenyayinlari', 'prefix': 'esenyayinlari', 'fernusCode_sifreli': '==QAiSmulgqD4cxwaBKNSbZQ', 'fernusCode_gercek': '3_6_10'}, 'fenomen': {'numara': 'fenomen', 'publisher': 'FENOMEN', 'pkxkname': 'fenomen', 'prefix': 'fenomen', 'fernusCode_sifreli': '==AB4lf+uPgyIJQMOrbN4uFl', 'fernusCode_gercek': '7_1_2'}, 'final': {'numara': 'final', 'publisher': 'Final Kurumsal Yayinlari', 'pkxkname': 'final', 'prefix': 'final', 'fernusCode_sifreli': '==QlkTjsY5tUPfEY60KKGgzz', 'fernusCode_gercek': '2_1_21'}, 'gunayyayinlari': {'numara': 'gunayyayinlari', 'publisher': 'Günay Yayınları', 'pkxkname': 'gunayyayinlari', 'prefix': 'gunayyayinlari', 'fernusCode_sifreli': '==AMc23nfN/+IG9rJbDB7guP', 'fernusCode_gercek': '9_4_8'}, 'hizyayinlari': {'numara': 'hizyayinlari', 'publisher': 'Hız Yayınları', 'pkxkname': 'hizyayinlari', 'prefix': 'hizyayinlari', 'fernusCode_sifreli': '==gNBvPrdq9uAUPH7mA4sbIu', 'fernusCode_gercek': '3_3_6'}, 'kurmay': {'numara': 'kurmay', 'publisher': 'More And More', 'pkxkname': 'kurmay', 'prefix': 'kurmay', 'fernusCode_sifreli': '==AnR1upKjObnIRg9TCHJzNP', 'fernusCode_gercek': '1_4_8'}, 'mavideniz': {'numara': 'mavideniz', 'publisher': 'Mavi Deniz Yayınları', 'pkxkname': 'mavideniz', 'prefix': 'mavideniz', 'fernusCode_sifreli': '==wjlfPITlzaJrlJtEvfNddI', 'fernusCode_gercek': '1_7_14'}, 'modelegitim': {'numara': 'modelegitim', 'publisher': 'Model Eğitim', 'pkxkname': 'modelegitim', 'prefix': 'modelegitim', 'fernusCode_sifreli': '==Azq7kXSfbLPgITSUt0QhH0', 'fernusCode_gercek': '7_14_22'}, 'mozaikyayinlari': {'numara': 'mozaikyayinlari', 'publisher': 'Mozaik Yayınları', 'pkxkname': 'mozaikyayinlari', 'prefix': 'mozaikyayinlari', 'fernusCode_sifreli': '==QSfM1nwZRaRqgLYvi0sjPr', 'fernusCode_gercek': '23_12_24'}, 'muba': {'numara': 'muba', 'publisher': 'MUBA', 'pkxkname': 'muba', 'prefix': 'muba', 'fernusCode_sifreli': '==Q2WphUNNMYDWvx8XOFGsYK', 'fernusCode_gercek': '4_7_14'}, 'oksijen': {'numara': 'oksijen', 'publisher': 'Oksijen Yayınları', 'pkxkname': 'oksijen', 'prefix': 'oksijen', 'fernusCode_sifreli': '==ATEqsLIa7ExwmWmfUYaVQt', 'fernusCode_gercek': '26_10_20'}, 'okyanus': {'numara': 'okyanus', 'publisher': 'Okyanus', 'pkxkname': 'okyanus', 'prefix': 'okyanus', 'fernusCode_sifreli': '==wm9r5wyVtUI9f6x3kbeaoK', 'fernusCode_gercek': '1_20_2'}, 'pruvaakademi': {'numara': 'pruvaakademi', 'publisher': 'Pruva Akademi', 'pkxkname': 'pruvaakademi', 'prefix': 'pruvaakademi', 'fernusCode_sifreli': '==wmJzlWu7X6MNVzeztmUF9W', 'fernusCode_gercek': '18_6_12'}, 'tammat': {'numara': 'tammat', 'publisher': 'Tammat', 'pkxkname': 'tammat', 'prefix': 'tammat', 'fernusCode_sifreli': '==AXruj34HL+qS3wplDY5sJ2', 'fernusCode_gercek': '1_1_2'}, 'toprak': {'numara': 'toprak', 'publisher': 'Toprak Yayıncılık', 'pkxkname': 'toprak', 'prefix': 'toprak', 'fernusCode_sifreli': '==A2MJ/AtSuzAjElex9c3Dbt', 'fernusCode_gercek': '9_5_10'}, 'unlulerkarmasi': {'numara': 'unlulerkarmasi', 'publisher': 'Ünlüler Karması', 'pkxkname': 'unlulerkarmasi', 'prefix': 'unlulerkarmasi', 'fernusCode_sifreli': '==QRPK1fVFC7Ep6W7xG7a92J', 'fernusCode_gercek': '26_12_24'}, 'yediiklim': {'numara': 'yediiklim', 'publisher': 'Yediiklim Yayınları', 'pkxkname': 'yediiklim', 'prefix': 'yediiklim', 'fernusCode_sifreli': '==w8YsC3ERMDlh6W37iRw2or', 'fernusCode_gercek': '2_26_20'}}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
PDF_DIR = r"c:\Z_Kitap_ve_Flip\PDF"
if not os.path.isdir(PDF_DIR):
    PDF_DIR = os.path.join(BASE_DIR, 'PDF_Mobil')
YAYINEVLERI_DIR = r"c:\Z_Kitap_ve_Flip\yayinevleri"
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

def pdf_dizinini_temizle():
    """Bulut sunucusunda disk ve bellek dolmasını önlemek için eski PDF'leri temizler"""
    try:
        if not os.path.isdir(PDF_DIR): return
        files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
        if len(files) > 10:
            files.sort(key=lambda x: os.path.getmtime(x))
            for f in files[:-10]:
                try: os.remove(f)
                except Exception: pass
    except Exception: pass

DEFAULT_UA = 'Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36'
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Fernus AES Şifreleme Sabitleri
IV = b'kxk101l0O1l0O1l0'
FALLBACK_MASTER = b'1l0O1l0O1l0O1l0O1l0O1l0O1l0O1l0O'

# Aktif indirme görevleri durum tablosu
TASKS = {}

def turkce_karakter_temizle(s):
    if not s: return ""
    tr_map = str.maketrans("çÇğĞıİöÖşŞüÜ", "cCgGiIoOsSuU")
    return str(s).translate(tr_map)

def extract_page_number(filename):
    m = re.findall(r'\d+', filename)
    return int(m[-1]) if m else 0

def gorsel_uzantisi(b):
    if not b or len(b) < 12: return None
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP': return '.webp'
    if b[:8] == b'\x89PNG\r\n\x1a\n': return '.png'
    if b[:3] == b'\xff\xd8\xff': return '.jpg'
    return None

def fix_url_template(url):
    url = url.strip()
    if '{page}' in url or '{p}' in url: return url
    new_url = re.sub(r'(/pages/)(\d+)(\.(webp|png|jpe?g|gif))', r'\1{page}\3', url, flags=re.IGNORECASE)
    if new_url != url: return new_url
    return re.sub(r'(p-l-|p-|_|/|page)(\d+)(\.(webp|png|jpe?g|gif))', r'\1{page}\3', url, flags=re.IGNORECASE)

# ==============================================================================
# FERNUS & FENOMEN KRİPTO VE YAYINEVİ FONKSİYONLARI
# ==============================================================================

def fernus_web_dec_string(s, key):
    raw = base64.b64decode(s.strip()[::-1])
    cipher = AES.new(key, AES.MODE_CBC, IV)
    pt = cipher.decrypt(raw)
    try: pt = unpad(pt, 16)
    except Exception: pass
    return pt

def fernus_web_aes_dec(raw, key):
    cipher = AES.new(key, AES.MODE_CBC, IV)
    pt = cipher.decrypt(raw)
    try: pt = unpad(pt, 16)
    except Exception: pass
    return pt

def fernus_web_make_key(fernus_code, master):
    k = fernus_code
    if len(k) < 32: k = k + master.decode('latin1')[:32 - len(k)]
    return k.encode('latin1')

def yayinevi_onbellek_al(numara):
    try:
        num_str = str(numara).lower()
        if num_str in YAYINEVLERI_DATA:
            kayit = YAYINEVLERI_DATA[num_str]
            pub = {'publisher': kayit.get('publisher', '?'), 'pkxkname': kayit.get('pkxkname', ''), 'fernusCode': kayit.get('fernusCode_sifreli', '')}
            fc = kayit.get('fernusCode_gercek', '')
            return pub, (fernus_web_make_key(fc, FALLBACK_MASTER) if fc else None)

        if os.path.isdir(YAYINEVLERI_DIR):
            json_yolu = os.path.join(YAYINEVLERI_DIR, f"{numara}.json")
            if os.path.isfile(json_yolu):
                with open(json_yolu, 'r', encoding='utf-8') as f: kayit = json.load(f)
                pub = {'publisher': kayit.get('publisher', '?'), 'pkxkname': kayit.get('pkxkname', ''), 'fernusCode': kayit.get('fernusCode_sifreli', '')}
                fc = kayit.get('fernusCode_gercek', '')
                return pub, (fernus_web_make_key(fc, FALLBACK_MASTER) if fc else None)
    except Exception:
        pass
    return None, None


def fernus_web_url_parse(url):
    url = url.strip()
    sonuc = {'url': url}
    m = re.match(r'(https?://cdn\.fernus\.net/(\d+)/zk/x/b/([^/]+))(?:/p-(?:l-)?(\d+)\.(webp|png|jpg|jpeg|gif))?', url, re.IGNORECASE)
    if m:
        base, numara, kitap = m.group(1), m.group(2), m.group(3)
        uzanti = m.group(5) or 'webp'
        sonuc.update({
            'root_path': f"https://cdn.fernus.net/{numara}/zk/x/p", 'prefix': None, 'numara': numara,
            'kitap_adi': kitap, 'yayinevi': f"Yayinevi_{numara}",
            'sayfa_pattern_soru': f"{base}/p-{{page}}.{uzanti}",
            'sayfa_pattern_cozum': f"{base}/p-l-{{page}}.{uzanti}", 'format': 'cdn'
        })
        return sonuc

    m = re.match(r'(https?://([^/]+)/(?:.*/)?bookszkitapx/([^/]+))(?:/{1,2}p-(?:l-)?(\d+)\.(webp|png|jpg|jpeg|gif))?', url, re.IGNORECASE)
    if m:
        base, domain, kitap = m.group(1), m.group(2), m.group(3)
        uzanti = m.group(5) or 'webp'
        domain_clean = domain.replace('www.', '').split('.')[0].lower()
        prefix = domain_clean
        if 'akillidefter' in domain_clean or 'ari' in domain_clean: prefix = 'ari'
        elif 'fenomen' in domain_clean: prefix = 'fenomen'
        elif 'altin' in domain_clean or 'karma' in domain_clean: prefix = 'altinkarma'
        elif domain_clean.endswith(('okul', 'yayin', 'yayincilik', 'dijital')):
            prefix = re.sub(r'(okul|yayin(?:cilik)?|dijital)$', '', domain_clean)

        slash_delim = '//' if '//p-' in url else '/'
        sonuc.update({
            'root_path': f"http://zkitapxeditor.fernus.net/publishers/{prefix}",
            'alt_root_path': base,
            'prefix': prefix, 'numara': None, 'kitap_adi': kitap, 'yayinevi': prefix.upper(),
            'sayfa_pattern_soru': f"{base}{slash_delim}p-{{page}}.{uzanti}",
            'sayfa_pattern_cozum': f"{base}{slash_delim}p-l-{{page}}.{uzanti}", 'format': 'custom_domain'
        })
        return sonuc
    return None

def fernus_web_publisher_json_al(info):
    anahtar = info.get('numara') or info.get('prefix')
    if anahtar:
        pub, _ = yayinevi_onbellek_al(anahtar)
        if pub: return pub
    if info.get('prefix'):
        for k in [info['prefix'], 'fenomen', 'ari']:
            pub, _ = yayinevi_onbellek_al(k)
            if pub: return pub

    BILINEN = {
        'fenomen': {'publisher': 'FENOMEN', 'pkxkname': 'fenomen', 'fernusCode': '==AB4lf+uPgyIJQMOrbN4uFl'},
        'ari': {'publisher': 'ARI', 'pkxkname': 'ari', 'fernusCode': '==AB0lfg8fW/h/V3Yf70V0Zk'},
        'altinkarma': {'publisher': 'Altın Karma Yayınları', 'pkxkname': 'altinkarma', 'fernusCode': '==QQEgQmMSJrk5Y84mrFcMFP'},
        'oksijen': {'publisher': 'Oksijen Yayınları', 'pkxkname': 'oksijen', 'fernusCode': '==ATEqsLIa7ExwmWmfUYaVQt'},
    }
    prefix = info.get('prefix', '')
    if prefix in BILINEN: return BILINEN[prefix]
    if info.get('numara') in BILINEN: return BILINEN[info['numara']]
    return None

def fernus_web_book_key_al(pub):
    if not pub: return None
    numara_veya_ad = pub.get('numara') or pub.get('pkxkname') or pub.get('prefix')
    if numara_veya_ad:
        _, bk = yayinevi_onbellek_al(numara_veya_ad)
        if bk: return bk
    fs = pub.get('fernusCode')
    if not fs: return None
    try:
        fc = fernus_web_dec_string(fs, FALLBACK_MASTER).decode('utf-8')
        return fernus_web_make_key(fc, FALLBACK_MASTER)
    except Exception: return None

def fernus_indir_ve_coz_sayfa(url, hedef_yol, book_key):
    headers = {'User-Agent': DEFAULT_UA, 'Referer': 'https://zkitapx.fernus.net/'}
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
                if r.status == 200:
                    raw = bytearray(r.read())
                    if len(raw) > 500:
                        pt = bytes(raw)
                        if gorsel_uzantisi(pt) is None:
                            tmp_raw = bytearray(raw)
                            for i in range(min(100, len(tmp_raw))): tmp_raw[i] = (256 - tmp_raw[i]) & 0xFF
                            if gorsel_uzantisi(bytes(tmp_raw)) is not None:
                                pt = bytes(tmp_raw)
                            elif book_key:
                                try:
                                    dec = fernus_web_aes_dec(bytes(raw), book_key)
                                    if gorsel_uzantisi(dec) is not None: pt = dec
                                except Exception: pass
                        ext = gorsel_uzantisi(pt)
                        if ext:
                            final_dest = hedef_yol if hedef_yol.endswith(ext) else hedef_yol + ext
                            with open(final_dest, 'wb') as f: f.write(pt)
                            return True
        except urllib.error.HTTPError as he:
            if he.code in (404, 500): return False
        except Exception:
            time.sleep(0.2)
    return False

def dijital_indir_sayfa(url, hedef_yol, referer=None, max_deneme=3):
    headers = {'User-Agent': DEFAULT_UA, 'Accept': 'image/*,*/*;q=0.8'}
    if referer: headers['Referer'] = referer
    for deneme in range(1, max_deneme + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12, context=SSL_CTX) as r:
                if r.status == 200:
                    data = r.read()
                    if len(data) > 500:
                        ext = gorsel_uzantisi(data) or '.jpg'
                        base_path = os.path.splitext(hedef_yol)[0]
                        final_path = base_path + ext
                        with open(final_path, 'wb') as f: f.write(data)
                        return True
        except urllib.error.HTTPError as he:
            if he.code in (404, 500): return False
        except Exception:
            time.sleep(0.3)
    return False

def gorsellerden_pdf_yap(gorsel_yollari, cikti_pdf_yolu, webp_kalite=100):
    if not gorsel_yollari:
        return False

    import gc

    # 1. Aşama: img2pdf ile diskteki dosya yollarından doğrudan akış (RAM: 0.3 MB, Süre: 1-2 sn)
    if img2pdf:
        try:
            with open(cikti_pdf_yolu, 'wb') as f:
                img2pdf.convert(gorsel_yollari, outputstream=f)
            gc.collect()
            pdf_dizinini_temizle()
            return True
        except Exception as e:
            print(f"img2pdf doğrudan dönüştürme uyarısı: {e}, uyumluluk moduna geçiliyor...")

    # 2. Aşama: Format uyuşmazlığı varsa (örn. özel PNG/alfa/bozuk meta),
    # sayfaları TEK TEK diske JPEG olarak normalize et (Belleği şişirmeden, RAM < 20MB)
    temp_conv_dir = os.path.join(os.path.dirname(cikti_pdf_yolu), f"conv_{uuid.uuid4().hex[:8]}")
    os.makedirs(temp_conv_dir, exist_ok=True)
    normalized_paths = []
    try:
        q = 95 if int(webp_kalite) >= 98 else int(webp_kalite)
        for idx, yol in enumerate(gorsel_yollari):
            target_jpg = os.path.join(temp_conv_dir, f"p_{idx:04d}.jpg")
            try:
                with Image.open(yol) as im:
                    if im.mode != 'RGB':
                        im = im.convert('RGB')
                    im.save(target_jpg, 'JPEG', quality=q, optimize=True)
                normalized_paths.append(target_jpg)
            except Exception as ex_norm:
                print(f"Sayfa normalize hatası ({yol}): {ex_norm}")
            if idx % 25 == 0:
                gc.collect()

        if normalized_paths and img2pdf:
            try:
                with open(cikti_pdf_yolu, 'wb') as f:
                    img2pdf.convert(normalized_paths, outputstream=f)
                pdf_dizinini_temizle()
                return True
            except Exception as e2:
                print(f"img2pdf normalize sonrası hata: {e2}")

        # 3. Aşama: Pillow Fallback (Son çare)
        if normalized_paths:
            try:
                first_img = Image.open(normalized_paths[0])
                other_imgs = [Image.open(p) for p in normalized_paths[1:]]
                first_img.save(cikti_pdf_yolu, "PDF", resolution=150.0, save_all=True, append_images=other_imgs)
                first_img.close()
                for im in other_imgs:
                    im.close()
                del other_imgs
                gc.collect()
                pdf_dizinini_temizle()
                return True
            except Exception as e3:
                print(f"Pillow fallback hatası: {e3}")
    finally:
        shutil.rmtree(temp_conv_dir, ignore_errors=True)
        gc.collect()

    return False


# ==============================================================================
# ANALİZ SERVİSLERİ
# ==============================================================================

def probe_sayfa_sayisi(pattern, referer=None, max_limit=450):
    """İkili arama (Binary Search) ile kitabın gerçek sayfa sayısını 1-3 saniyede bulur"""
    headers = {'User-Agent': DEFAULT_UA}
    if referer: headers['Referer'] = referer

    def _var_mi(p):
        u = pattern.replace('{page}', str(p)).replace('{p}', str(p))
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5, context=SSL_CTX) as r:
                return r.status == 200
        except Exception:
            return False

    if not _var_mi(1):
        if _var_mi(0): return 1
        return 0

    low, high, en_son = 1, max_limit, 1
    while low <= high:
        mid = (low + high) // 2
        if _var_mi(mid):
            en_son = mid
            low = mid + 1
        else:
            high = mid - 1
    return en_son


def analiz_et(girdi_url):
    girdi = girdi_url.strip()

    # 1. Altın Karne
    if 'altinkarne.com' in girdi.lower() or (girdi.isdigit() and len(girdi) < 6):
        m = re.search(r'book-app/(\d+)', girdi) or re.search(r'bookId=(\d+)', girdi)
        book_id = m.group(1) if m else (girdi if girdi.isdigit() else None)
        if not book_id: raise ValueError("Altın Karne kitap ID tespit edilemedi.")

        api_url = f"https://www.altinkarne.com/bookapp/GetBook?bookId={book_id}"
        req = urllib.request.Request(api_url, headers={'User-Agent': DEFAULT_UA})
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            data = json.loads(r.read().decode('utf-8'))

        b = data.get('books', {}).get('book', {})
        baslik = b.get('bookName') or f"AltinKarne_{book_id}"
        has_cozum = bool(b.get('hasCozum', True))
        items = b.get('items') or b.get('page') or []
        sayfalar = []

        if isinstance(items, list) and items:
            total_pages = len(items)
            for item in items:
                cnt = item.get('content', {}) if isinstance(item, dict) else {}
                p_num = int(cnt.get('page') or cnt.get('orginalPageNumber') or len(sayfalar) + 1)
                s_url = cnt.get('url') or f"https://www.altinkarne.com/bookapp/GetImage?bookId={book_id}&page={p_num}.jpg"
                c_url = cnt.get('cozumUrl') or f"https://www.altinkarne.com/bookapp/GetCozumImage?bookId={book_id}&page={p_num}.jpg"
                sayfalar.append({'page': p_num, 'soru_url': s_url, 'cozum_url': c_url})
        else:
            p_val = b.get('page')
            total_pages = int(p_val) if isinstance(p_val, (int, str)) and str(p_val).isdigit() else 240
            for p_num in range(1, total_pages + 1):
                sayfalar.append({
                    'page': p_num,
                    'soru_url': f"https://www.altinkarne.com/bookapp/GetImage?bookId={book_id}&page={p_num}.jpg",
                    'cozum_url': f"https://www.altinkarne.com/bookapp/GetCozumImage?bookId={book_id}&page={p_num}.jpg"
                })

        kapak_url = f"https://www.altinkarne.com/bookapp/GetImage?bookId={book_id}&page=1.jpg"
        return {
            'platform': 'ALTIN_KARNE',
            'platform_label': 'Altın Karne',
            'book_id': book_id,
            'title': baslik,
            'pages_count': total_pages,
            'has_solution': has_cozum,
            'cover_url': kapak_url,
            'pages': sayfalar
        }

    # 2. Sınav Dijital
    uuid_match = re.search(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', girdi)
    if 'sinavdijital.com' in girdi.lower() or uuid_match:
        uuid_str = uuid_match.group(0) if uuid_match else None
        if not uuid_str: raise ValueError("Sınav Dijital belge kodu tespit edilemedi.")

        title = f"SinavDijital_{uuid_str[:8]}"
        try:
            req = urllib.request.Request(f"https://www.sinavdijital.com/api/documents/{uuid_str}/", headers={'User-Agent': DEFAULT_UA})
            with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as r:
                doc = json.loads(r.read().decode('utf-8')).get('document', {})
                if doc.get('title'): title = doc['title']
        except Exception: pass

        req = urllib.request.Request(f"https://www.sinavdijital.com/api/document/{uuid_str}/pages/", headers={'User-Agent': DEFAULT_UA})
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            pages_data = json.loads(r.read().decode('utf-8')).get('pages', [])

        sayfalar = []
        if pages_data:
            total_pages = len(pages_data)
            for p_item in pages_data:
                p_num = int(p_item.get('page_number', 1))
                sayfalar.append({
                    'page': p_num,
                    'soru_url': f"https://www.sinavdijital.com/api/bookapp/GetImage?bookId={uuid_str}&page={p_num}.png",
                    'cozum_url': f"https://www.sinavdijital.com/api/bookapp/GetCozumImage?bookId={uuid_str}&page={p_num}.png"
                })
        else:
            total_pages = 60
            for p_num in range(1, 61):
                sayfalar.append({
                    'page': p_num,
                    'soru_url': f"https://www.sinavdijital.com/api/bookapp/GetImage?bookId={uuid_str}&page={p_num}.png",
                    'cozum_url': f"https://www.sinavdijital.com/api/bookapp/GetCozumImage?bookId={uuid_str}&page={p_num}.png"
                })

        kapak_url = f"https://www.sinavdijital.com/api/bookapp/GetImage?bookId={uuid_str}&page=1.png"
        return {
            'platform': 'SINAV_DIJITAL',
            'platform_label': 'Sınav Dijital',
            'book_id': uuid_str,
            'title': title,
            'pages_count': total_pages,
            'has_solution': True,
            'cover_url': kapak_url,
            'pages': sayfalar
        }

    # 3. Fernus & Fenomen Web Z-Kitap
    if any(k in girdi.lower() for k in ('cdn.fernus.net', 'bookszkitapx', 'akillidefter.com.tr', 'fenomenokul.com', 'zkitapx')):
        info = fernus_web_url_parse(girdi)
        if not info: raise ValueError("Fernus Web URL formatı tanınamadı.")
        pub = fernus_web_publisher_json_al(info)
        book_key = fernus_web_book_key_al(pub)

        title = info.get('kitap_adi', 'Fernus_Kitap')
        ref = "https://zkitapx.fernus.net/"

        gercek_sayfa = probe_sayfa_sayisi(info['sayfa_pattern_soru'], referer=ref, max_limit=450)
        if gercek_sayfa < 1:
            for alt_ext in ['jpg', 'png']:
                alt_pat = re.sub(r'\.(webp|png|jpe?g)$', f'.{alt_ext}', info['sayfa_pattern_soru'], flags=re.IGNORECASE)
                alt_c = probe_sayfa_sayisi(alt_pat, referer=ref, max_limit=450)
                if alt_c > 0:
                    info['sayfa_pattern_soru'] = alt_pat
                    info['sayfa_pattern_cozum'] = re.sub(r'\.(webp|png|jpe?g)$', f'.{alt_ext}', info['sayfa_pattern_cozum'], flags=re.IGNORECASE)
                    gercek_sayfa = alt_c
                    break

        total_pages = gercek_sayfa if gercek_sayfa > 0 else 60

        sayfalar = []
        for p in range(1, total_pages + 1):
            s_u = info['sayfa_pattern_soru'].replace('{page}', str(p))
            c_u = info['sayfa_pattern_cozum'].replace('{page}', str(p))
            sayfalar.append({'page': p, 'soru_url': s_u, 'cozum_url': c_u})

        kapak = sayfalar[0]['soru_url'] if sayfalar else ""
        return {
            'platform': 'FERNUS_WEB',
            'platform_label': f"Fernus Web ({info.get('yayinevi', 'Z-Kitap')})",
            'book_id': info.get('kitap_adi', 'fernus'),
            'title': title,
            'pages_count': total_pages,
            'has_solution': True,
            'cover_url': kapak,
            'book_key_hex': book_key.hex() if book_key else '',
            'pages': sayfalar
        }

    # 4. SmartBook / Newton / Nitelik / Supara (Obro API)
    m_smart = re.search(r'(?:smartBook/|guid=|bookId=|book_id=)([a-zA-Z0-9\-]+)', girdi, re.IGNORECASE)
    is_smart = any(k in girdi.lower() for k in ('smartbook', 'newtondijital', 'nitelik', 'supara', 'viewbook')) or m_smart
    if is_smart and ('fliphtml5' not in girdi.lower()):
        parsed = urllib.parse.urlparse(girdi)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        book_id = m_smart.group(1) if m_smart else "370"
        api_url = f"{base_url}/api/smartbook/SbPublicGuess/GetSmartBook?bookId={book_id}&includePageItems=true"

        req = urllib.request.Request(api_url, headers={'User-Agent': DEFAULT_UA})
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            data = json.loads(r.read().decode('utf-8'))

        title = data.get('title') or data.get('name') or f"SmartBook_{book_id}"
        pages = []
        for idx, p in enumerate(data.get('pages', []), 1):
            if p.get('pageImageUrl'):
                u = p['pageImageUrl']
                u_full = u if u.startswith('http') else f"{base_url}/{u.lstrip('/')}"
                pages.append({'page': idx, 'soru_url': u_full, 'cozum_url': None})

        kapak = pages[0]['soru_url'] if pages else ""
        label = "Newton SmartBook" if "newton" in girdi.lower() else ("Nitelik SmartBook" if "nitelik" in girdi.lower() else "Supara FlipBook")
        return {
            'platform': 'SUPARA_FLIP',
            'platform_label': label,
            'book_id': str(book_id),
            'title': title,
            'pages_count': len(pages),
            'has_solution': False,
            'cover_url': kapak,
            'pages': pages
        }

    # 5. İmpark Web Z-Kitap
    if any(k in girdi.lower() for k in ('/pages/', '/uploads/', 'impark', 'ozdebirdijital', 'yargidersarkadasim')):
        fixed_url = fix_url_template(girdi)
        clean_no_query = girdi.split('?')[0].rstrip('/')
        parcalar = [p for p in clean_no_query.split('/') if p and not p.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.gif'))]
        kitap_adi = f"Impark_{parcalar[-1]}" if parcalar else "Impark_Kitap"

        parsed_imp = urllib.parse.urlparse(girdi)
        ref = f"{parsed_imp.scheme}://{parsed_imp.netloc}/"

        gercek_sayfa = probe_sayfa_sayisi(fixed_url, referer=ref, max_limit=450)
        total_pages = gercek_sayfa if gercek_sayfa > 0 else 50

        pages = []
        for p in range(1, total_pages + 1):
            p_url = fixed_url.replace('{page}', str(p)).replace('{p}', str(p))
            pages.append({'page': p, 'soru_url': p_url, 'cozum_url': None})

        return {
            'platform': 'IMPARK_WEB',
            'platform_label': 'İmpark Web',
            'book_id': kitap_adi,
            'title': kitap_adi,
            'pages_count': total_pages,
            'has_solution': False,
            'cover_url': pages[0]['soru_url'] if pages else '',
            'referer': ref,
            'pages': pages
        }

    # 6. FlipHTML5 (Jet Motoru - Otomatik Sayfa ve Şifre Çözücü)
    if 'fliphtml5.com' in girdi.lower():
        m = re.search(r'fliphtml5\.com/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)', girdi)
        if m:
            u_code, b_code = m.group(1), m.group(2)
            book_url = f"https://online.fliphtml5.com/{u_code}/{b_code}/"
            title = f"FlipHTML5_{u_code}_{b_code}"
            pages = []

            # 1. Aşama: Headless Chrome ile dinamik/WASM ile şifrelenmiş sayfa listesini çöz
            driver = None
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options

                chrome_opts = Options()
                chrome_opts.add_argument('--headless=new')
                chrome_opts.add_argument('--no-sandbox')
                chrome_opts.add_argument('--disable-dev-shm-usage')
                chrome_opts.add_argument('--disable-gpu')
                chrome_opts.add_argument(f'user-agent={DEFAULT_UA}')

                driver = webdriver.Chrome(options=chrome_opts)
                driver.get(book_url)
                time.sleep(3)

                js_extract = '''
                var urls = [];
                var base = (window.bookConfig && window.bookConfig.bookBaseURL) || location.href.replace(/#.*$/, '');
                if(!base.endsWith('/')) base += '/';

                var pList = null;
                if (Array.isArray(window.fliphtml5_pages)) pList = window.fliphtml5_pages;
                else if (window.bookConfig && Array.isArray(window.bookConfig.pages)) pList = window.bookConfig.pages;
                else if (window.htmlConfig && Array.isArray(window.htmlConfig.pageEditor)) pList = window.htmlConfig.pageEditor;

                if (pList && pList.length > 0) {
                    for(var i=0; i<pList.length; i++) {
                        var p = pList[i];
                        var u = null;
                        if(typeof p === 'string') u = p;
                        else if(typeof p === 'object' && p !== null) u = p.n || p.large || p.normal || p.src || p.l || p.ptf;
                        if(Array.isArray(u)) u = u[0];
                        if(u) {
                            if(u.startsWith('http')) urls.push(u);
                            else {
                                var rel = u.replace(/\\\\/g, '/');
                                while(rel.startsWith('./')) rel = rel.substring(2);
                                if(rel.startsWith('/')) rel = rel.substring(1);
                                urls.push(base + rel);
                            }
                        }
                    }
                }
                var t = document.title || '';
                return {title: t, urls: urls};
                '''

                res = driver.execute_script(js_extract)
                if res:
                    raw_title = res.get('title', '')
                    if raw_title and 'Just a moment' not in raw_title and raw_title.strip() != 'FlipHTML5':
                        title = re.sub(r'[\\/*?:"<>|]', '_', raw_title).strip()

                    found_urls = res.get('urls', [])
                    for idx, u in enumerate(found_urls, 1):
                        pages.append({'page': idx, 'soru_url': u, 'cozum_url': None})
            except Exception as ex:
                print(f"FlipHTML5 Headless Çözüm Hatası: {ex}")
            finally:
                if driver:
                    try: driver.quit()
                    except Exception: pass

            # 2. Aşama Fallback: Headless sayfaları çekemediyse olası formatları yokla
            if not pages:
                candidates = [
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/large/1.webp",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/large/1.jpg",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/mobile/1.webp",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/files/mobile/1.jpg",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/1.webp",
                    f"https://online.fliphtml5.com/{u_code}/{b_code}/1.jpg"
                ]
                working_tpl = None
                for cand in candidates:
                    try:
                        req_c = urllib.request.Request(cand, headers={'User-Agent': DEFAULT_UA, 'Referer': book_url})
                        with urllib.request.urlopen(req_c, timeout=3, context=SSL_CTX) as rc:
                            if rc.status == 200 and len(rc.read()) > 500:
                                working_tpl = cand.replace('/1.', '/{page}.')
                                break
                    except Exception:
                        pass

                if not working_tpl:
                    working_tpl = f"https://online.fliphtml5.com/{u_code}/{b_code}/files/large/{{page}}.jpg"

                for idx in range(1, 401):
                    pages.append({'page': idx, 'soru_url': working_tpl.replace('{page}', str(idx)), 'cozum_url': None})

            kapak = pages[0]['soru_url'] if pages else ""
            return {
                'platform': 'FLIPHTML5',
                'platform_label': 'FlipHTML5 Jet',
                'book_id': f"{u_code}_{b_code}",
                'title': title,
                'pages_count': len(pages),
                'has_solution': False,
                'cover_url': kapak,
                'referer': book_url,
                'pages': pages
            }

    raise ValueError("Girilen link desteklenen bir formatta değil. Fernus, Newton, İmpark, Supara, FlipHTML5, Altın Karne veya Sınav Dijital linki giriniz.")

# ==============================================================================
# ARKA PLAN İNDİRME MOTORU
# ==============================================================================

def benzersiz_pdf_adi(dizin, baslik_temiz, son_ek=""):
    ek = f" - {son_ek}" if son_ek else ""
    ad = f"[Mobil PDF] {baslik_temiz}{ek}" if not baslik_temiz.startswith("[Mobil PDF]") else f"{baslik_temiz}{ek}"
    hedef = f"{ad}.pdf"
    sayac = 1
    while os.path.exists(os.path.join(dizin, hedef)):
        sayac += 1
        hedef = f"{ad} ({sayac}).pdf"
    return hedef

def indirme_gorevi_baslat(task_id, kitap_verisi, mod=1, webp_kalite=100):
    TASKS[task_id] = {
        'status': 'running',
        'progress': 0,
        'message': 'İndirme hazırlanıyor...',
        'completed': 0,
        'total': 0,
        'pdf_files': []
    }

    def run():
        try:
            pages = kitap_verisi['pages']
            temiz_baslik = re.sub(r'[\\/*?:"<>|]', '_', str(kitap_verisi['title'])).strip()[:100]
            temp_dir = os.path.join(PDF_DIR, f"temp_{uuid.uuid4().hex[:8]}")
            os.makedirs(temp_dir, exist_ok=True)

            ref = "https://www.altinkarne.com/" if kitap_verisi['platform'] == 'ALTIN_KARNE' else None
            if kitap_verisi['platform'] == 'SINAV_DIJITAL': ref = "https://www.sinavdijital.com/"
            if kitap_verisi['platform'] == 'FLIPHTML5': ref = kitap_verisi.get('referer') or "https://online.fliphtml5.com/"
            if kitap_verisi['platform'] == 'IMPARK_WEB': ref = kitap_verisi.get('referer')

            is_fernus = kitap_verisi['platform'] == 'FERNUS_WEB'
            bk_bytes = bytes.fromhex(kitap_verisi.get('book_key_hex', '')) if is_fernus and kitap_verisi.get('book_key_hex') else None

            tasks = []
            if mod in (1, 3):
                for p in pages:
                    dest = os.path.join(temp_dir, f"s_{p['page']:04d}")
                    tasks.append(('SORU', p['page'], p['soru_url'], dest))
            if mod in (2, 3) and kitap_verisi.get('has_solution'):
                for p in pages:
                    if p.get('cozum_url'):
                        dest = os.path.join(temp_dir, f"c_{p['page']:04d}")
                        tasks.append(('COZUM', p['page'], p['cozum_url'], dest))

            toplam = len(tasks)
            TASKS[task_id]['total'] = toplam
            tamamlanan = 0

            with ThreadPoolExecutor(max_workers=8) as ex:
                if is_fernus:
                    futs = {ex.submit(fernus_indir_ve_coz_sayfa, t[2], t[3], bk_bytes): t for t in tasks}
                else:
                    futs = {ex.submit(dijital_indir_sayfa, t[2], t[3], ref): t for t in tasks}

                for f in as_completed(futs):
                    tamamlanan += 1
                    yuzde = int((tamamlanan / toplam) * 85)
                    TASKS[task_id]['completed'] = tamamlanan
                    TASKS[task_id]['progress'] = yuzde
                    TASKS[task_id]['message'] = f"Sayfalar işleniyor... ({tamamlanan}/{toplam})"

            TASKS[task_id]['message'] = "Yüksek kaliteli PDF oluşturuluyor..."
            TASKS[task_id]['progress'] = 90
            uretilen_pdfler = []

            def _is_valid_file(fp):
                try:
                    with open(fp, 'rb') as f:
                        return gorsel_uzantisi(f.read(16)) is not None
                except Exception:
                    return False

            all_files = os.listdir(temp_dir)
            if mod in (1, 3):
                soru_img = [os.path.join(temp_dir, fn) for fn in all_files if fn.startswith('s_') and _is_valid_file(os.path.join(temp_dir, fn))]
                soru_img.sort(key=lambda x: extract_page_number(os.path.basename(x)))
                if soru_img:
                    out_name = benzersiz_pdf_adi(PDF_DIR, temiz_baslik)
                    out_pdf = os.path.join(PDF_DIR, out_name)
                    if gorsellerden_pdf_yap(soru_img, out_pdf, webp_kalite=webp_kalite):
                        uretilen_pdfler.append(out_name)

            if mod in (2, 3) and kitap_verisi.get('has_solution'):
                cozum_img = [os.path.join(temp_dir, fn) for fn in all_files if fn.startswith('c_') and _is_valid_file(os.path.join(temp_dir, fn))]
                cozum_img.sort(key=lambda x: extract_page_number(os.path.basename(x)))
                if cozum_img:
                    out_cozum_name = benzersiz_pdf_adi(PDF_DIR, temiz_baslik, son_ek="Çözümler")
                    out_cozum_pdf = os.path.join(PDF_DIR, out_cozum_name)
                    if gorsellerden_pdf_yap(cozum_img, out_cozum_pdf, webp_kalite=webp_kalite):
                        uretilen_pdfler.append(out_cozum_name)

            shutil.rmtree(temp_dir, ignore_errors=True)

            if uretilen_pdfler:
                refresh_short_map()
                TASKS[task_id]['status'] = 'completed'
                TASKS[task_id]['progress'] = 100
                TASKS[task_id]['message'] = f"İşlem Başarılı! {len(uretilen_pdfler)} adet PDF hazırlandı."
                TASKS[task_id]['pdf_files'] = uretilen_pdfler
                TASKS[task_id]['pdf_files_info'] = [
                    {
                        'name': fn,
                        'url': f"/pdf/{urllib.parse.quote(fn)}",
                        'short_url': f"/d/{SHORT_REVERSE.get(fn, '1')}"
                    }
                    for fn in uretilen_pdfler
                ]
            else:
                TASKS[task_id]['status'] = 'failed'
                TASKS[task_id]['message'] = "Sayfalar indirilemedi veya PDF oluşturulamadı."

        except Exception as e:
            TASKS[task_id]['status'] = 'failed'
            TASKS[task_id]['message'] = f"Hata: {str(e)}"

    t = threading.Thread(target=run, daemon=True)
    t.start()

def toplu_indirme_gorevi_baslat(task_id, kitap_listesi, mod=1, webp_kalite=100):
    TASKS[task_id] = {
        'status': 'running',
        'progress': 0,
        'message': f"Toplu indirme başlıyor (Toplam {len(kitap_listesi)} kitap)...",
        'completed': 0,
        'total': len(kitap_listesi),
        'pdf_files': [],
        'pdf_files_info': []
    }

    def run():
        total_books = len(kitap_listesi)
        all_produced = []
        for i, b_data in enumerate(kitap_listesi, 1):
            sub_id = f"{task_id}_{i}"
            b_title = b_data.get('title', 'Kitap')
            clean_b_title = b_title[:32] + '...' if len(b_title) > 32 else b_title
            TASKS[task_id]['message'] = f"[{i}/{total_books}] {clean_b_title} başlatılıyor..."
            TASKS[task_id]['progress'] = max(1, int(((i - 1) / total_books) * 95))

            indirme_gorevi_baslat(sub_id, b_data, mod=mod, webp_kalite=webp_kalite)

            while TASKS.get(sub_id, {}).get('status') == 'running':
                st = TASKS.get(sub_id, {})
                sub_prog = st.get('progress', 0)
                sub_comp = st.get('completed', 0)
                sub_tot = st.get('total', 0)
                sub_msg = st.get('message', '')

                # Kitabın kendi içindeki sayfa ilerlemesini toplu ilerlemeye yansıt
                overall_prog = int(((i - 1) + (sub_prog / 100.0)) / total_books * 95)
                TASKS[task_id]['progress'] = max(1, min(95, overall_prog))
                TASKS[task_id]['completed'] = sub_comp
                TASKS[task_id]['total'] = sub_tot
                TASKS[task_id]['message'] = f"[{i}/{total_books}] {clean_b_title}: {sub_msg}"
                time.sleep(0.4)

            sub_task = TASKS.get(sub_id, {})
            if sub_task.get('status') == 'completed':
                for fn in sub_task.get('pdf_files', []):
                    if fn not in all_produced:
                        all_produced.append(fn)
            else:
                print(f"[Toplu İndirme] Alt görev {sub_id} ({b_title}) tamamlanamadı: {sub_task.get('message')}")

            TASKS[task_id]['pdf_files'] = list(all_produced)

        if all_produced:
            refresh_short_map()
            TASKS[task_id]['status'] = 'completed'
            TASKS[task_id]['progress'] = 100
            TASKS[task_id]['message'] = f"Toplu İşlem Tamamlandı! {len(all_produced)} adet PDF hazırlandı."
            TASKS[task_id]['pdf_files'] = all_produced
            TASKS[task_id]['pdf_files_info'] = [
                {
                    'name': fn,
                    'url': f"/pdf/{urllib.parse.quote(fn)}",
                    'short_url': f"/d/{SHORT_REVERSE.get(fn, '1')}"
                }
                for fn in all_produced
            ]
        else:
            TASKS[task_id]['status'] = 'failed'
            TASKS[task_id]['progress'] = 0
            TASKS[task_id]['message'] = "Toplu indirmedeki hiçbir kitap PDF'e dönüştürülemedi."

    t = threading.Thread(target=run, daemon=True)
    t.start()

# ==============================================================================
# HTTP SUNUCU İŞLEYİCİSİ
# ==============================================================================

SHORT_MAP = {}
SHORT_REVERSE = {}

def refresh_short_map():
    global SHORT_MAP, SHORT_REVERSE
    SHORT_MAP.clear()
    SHORT_REVERSE.clear()
    if os.path.isdir(PDF_DIR):
        files = [fn for fn in sorted(os.listdir(PDF_DIR)) if fn.lower().endswith('.pdf')]
        for idx, fn in enumerate(files, 1):
            sid = str(idx)
            SHORT_MAP[sid] = fn
            SHORT_REVERSE[fn] = sid

class MobileServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/library':
            refresh_short_map()
            files = []
            if os.path.isdir(PDF_DIR):
                for fn in os.listdir(PDF_DIR):
                    if fn.lower().endswith('.pdf'):
                        fp = os.path.join(PDF_DIR, fn)
                        sz = os.path.getsize(fp) / (1024 * 1024)
                        mtime = os.path.getmtime(fp)
                        sid = SHORT_REVERSE.get(fn, "1")
                        files.append({
                            'name': fn,
                            'id': sid,
                            'size_mb': f"{sz:.1f} MB",
                            'date': time.strftime("%d.%m.%Y %H:%M", time.localtime(mtime)),
                            'url': f"/pdf/{urllib.parse.quote(fn)}",
                            'short_url': f"/d/{sid}"
                        })
            files.sort(key=lambda x: x['date'], reverse=True)
            self._json_response({'success': True, 'files': files})
            return

        if path == '/api/progress':
            qs = urllib.parse.parse_qs(parsed.query)
            tid = qs.get('id', [None])[0]
            if tid and tid in TASKS:
                self._json_response({'success': True, 'task': TASKS[tid]})
            else:
                self._json_response({'success': False, 'message': 'Görev bulunamadı'})
            return

        if path.startswith('/d/'):
            sid = path[3:].split('?')[0].split('/')[0]
            refresh_short_map()
            fname = SHORT_MAP.get(sid)
            if fname:
                fp = os.path.join(PDF_DIR, fname)
                if os.path.isfile(fp):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/pdf')
                    safe_ascii = turkce_karakter_temizle(fname).encode('ascii', 'ignore').decode('ascii') or "kitap.pdf"
                    encoded_utf8 = urllib.parse.quote(fname)
                    self.send_header('Content-Disposition', f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded_utf8}')
                    self.send_header('Content-Length', str(os.path.getsize(fp)))
                    self.end_headers()
                    with open(fp, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
            self.send_error(404, "Kisa link bulunamadi")
            return

        if path == '/api/download_pdf' or path.startswith('/pdf/'):
            fname = None
            if path.startswith('/pdf/'):
                fname = urllib.parse.unquote(path[5:])
            else:
                qs = urllib.parse.parse_qs(parsed.query)
                fname = qs.get('name', [None])[0]

            if fname:
                fp = os.path.join(PDF_DIR, os.path.basename(fname))
                if os.path.isfile(fp):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/pdf')
                    safe_ascii = turkce_karakter_temizle(os.path.basename(fname)).encode('ascii', 'ignore').decode('ascii') or "kitap.pdf"
                    encoded_utf8 = urllib.parse.quote(os.path.basename(fname))
                    self.send_header('Content-Disposition', f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded_utf8}')
                    self.send_header('Content-Length', str(os.path.getsize(fp)))
                    self.end_headers()
                    with open(fp, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
            self.send_error(404, "Dosya bulunamadi")
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else '{}'
        data = json.loads(body) if body else {}

        if parsed.path == '/api/analyze':
            raw_url = data.get('url', '').strip()
            if not raw_url:
                self._json_response({'success': False, 'message': 'Lütfen geçerli bir link veya ID girin.'}, status=400)
                return

            # Tüm http(s) linklerini regex ile metinden çek (boşluk, virgül, satır sonu fark etmeksizin)
            found_urls = re.findall(r'https?://[^\s,;"\'<>]+', raw_url)
            if not found_urls:
                # URL formatında değilse satırlara, boşluklara veya virgüllere böl (örn. sadece kitap ID'leri girilmişse: 647 648)
                tokens = [s.strip() for s in re.split(r'[\r\n,;\s]+', raw_url) if s.strip() and not s.strip().startswith('#')]
            else:
                tokens = found_urls

            # Tekilleştir
            seen = set()
            unique_tokens = []
            for t in tokens:
                if t not in seen:
                    seen.add(t)
                    unique_tokens.append(t)

            if len(unique_tokens) > 1:
                # Toplu Link Analizi
                books = []
                errors = []
                for u in unique_tokens:
                    try:
                        b = analiz_et(u)
                        books.append(b)
                    except Exception as e:
                        errors.append(f"{u[:40]}...: {str(e)}")
                if not books:
                    self._json_response({'success': False, 'message': f"Hiçbir link çözülemedi:\n" + "\n".join(errors)}, status=400)
                    return
                self._json_response({'success': True, 'is_batch': True, 'books': books, 'errors': errors})
                return
            else:
                target_url = unique_tokens[0] if unique_tokens else raw_url
                try:
                    res = analiz_et(target_url)
                    self._json_response({'success': True, 'is_batch': False, 'data': res})
                except Exception as e:
                    self._json_response({'success': False, 'message': str(e)}, status=400)
                return

        if parsed.path == '/api/start_download':
            kitap_data = data.get('book_data')
            mod = int(data.get('mod', 1))
            kalite = int(data.get('quality', 100))
            if not kitap_data:
                self._json_response({'success': False, 'message': 'Kitap verisi eksik.'}, status=400)
                return
            tid = str(uuid.uuid4())
            indirme_gorevi_baslat(tid, kitap_data, mod=mod, webp_kalite=kalite)
            self._json_response({'success': True, 'task_id': tid})
            return

        if parsed.path == '/api/start_batch_download':
            books = data.get('books', [])
            mod = int(data.get('mod', 1))
            kalite = int(data.get('quality', 100))
            if not books:
                self._json_response({'success': False, 'message': 'Kitap listesi eksik.'}, status=400)
                return
            batch_id = str(uuid.uuid4())
            toplu_indirme_gorevi_baslat(batch_id, books, mod=mod, webp_kalite=kalite)
            self._json_response({'success': True, 'task_id': batch_id})
            return

        if parsed.path == '/api/delete_pdf':
            fname = data.get('name')
            if fname:
                fp = os.path.join(PDF_DIR, os.path.basename(fname))
                if os.path.isfile(fp):
                    try:
                        os.remove(fp)
                        refresh_short_map()
                        self._json_response({'success': True})
                        return
                    except Exception as e:
                        self._json_response({'success': False, 'message': str(e)}, status=500)
                        return
            self._json_response({'success': False, 'message': 'Dosya bulunamadı'}, status=404)
            return

        self.send_error(404, "Endpoint bulunamadi")

    def _json_response(self, obj, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode('utf-8'))

def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def run_port_listener(p):
    try:
        server = ThreadingHTTPServer(('0.0.0.0', p), MobileServerHandler)
        server.serve_forever()
    except Exception as e:
        print(f"Port {p} dinlenemedi: {e}")

def main():
    import sys
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    local_ip = get_local_ip()
    main_port = int(os.environ.get('PORT', 5050))

    # Port 80'i sadece yerel Windows ortamında ve ana port farklıysa dene
    if main_port != 80 and not os.environ.get('PORT'):
        t80 = threading.Thread(target=run_port_listener, args=(80,), daemon=True)
        t80.start()

    print("\n" + "="*60)
    print(" [OK] Z KITAP MOBIL SUNUCUSU BASLATILDI (v2.7)")
    print("="*60)
    print(f" * Ana Servis Portu:     http://{local_ip}:{main_port}")
    print(f" * Bilgisayardan Erisim: http://localhost:{main_port}")
    print("="*60 + "\n")

    # Ana servisi calistir
    run_port_listener(main_port)

if __name__ == '__main__':
    main()
