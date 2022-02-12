'''
Ini adalah script untuk mengubah pdf lampiran hasil CPNS jadi csv
Caveat: kalo langsung prosess 20rb halaman, agak keselek di tengah, jadi mending di-iterate beberapa halaman
Saya yakin ada cara yang lebih elegan. Feel free to give me any suggestions
Cara run
python export_data_to_csv.py index_halaman_start index_halaman_end
Misal
python export_data_to_csv.py 0 100
'''

from ast import And
import pdfplumber
import pandas as pd
import datetime as dt
import sys


def check_formasi_kosong_page(page):
    '''
    Fungsi untuk mengecek keberadaan tabel perorangan
    Input: page (ex: pdf.pages[0])
    Output:
        - found (binary, iya tidaknya sebuah halaman punya tabel perorangan)
        - df_returned (tabel perorangan jika ada)
    '''
    found = False
    df_returned = pd.DataFrame()
    tms1_terbaik = 0
    for table in page.extract_tables():
        df = pd.DataFrame(table)
        if (df.shape[1] == 11) & (df.shape[0] == 5):

            df_returned = df

            jumlah_formasi = int(df.iloc[4, 1])
            lulus_akhir = int(df.iloc[4, 10])
            jumlah_tms1 = int(df.iloc[4, 8])
            sisa_formasi = jumlah_formasi - lulus_akhir

            if sisa_formasi > 0:
                found = True
                if sisa_formasi < jumlah_tms1:
                    tms1_terbaik = sisa_formasi
                else:
                    tms1_terbaik = jumlah_tms1

    return found, tms1_terbaik, df_returned


def check_for_detail_tables(page):
    '''
    Fungsi untuk mengecek keberadaan tabel perorangan
    Input: page (ex: pdf.pages[0])
    Output:
        - found (binary, iya tidaknya sebuah halaman punya tabel perorangan)
        - df_returned (tabel perorangan jika ada)
    '''

    # print("check_for_detail_tables")

    found = False
    df_returned = pd.DataFrame()
    for table in page.extract_tables():
        df = pd.DataFrame(table)
        if (df.shape[1] == 11) & (df.shape[0] > 16):
            found = True
            # print("page : "+str(page)+"found : "+str(found))

            df_returned = df
    return found, df_returned


def check_for_jabatan(page):
    '''
    Fungsi untuk mengecek keberadaan informasi lowongan
    Input: page (ex: pdf.pages[0])
    Output:
        - dicitionary berisi informasi lowongan
    '''
    if "Lokasi Formasi :" in page.extract_text():
        text = page.extract_text()
        pendidikan = page.extract_tables()[1][0][1]
        jabatan_strings = text.split("Jabatan : ")[1].split("Lokasi")[0]
        lokasi_front = ""
        jabatan = jabatan_strings.split("\n")[0]

        if len(jabatan_strings.split("\n")) > 1:
            lokasi_front = " ".join(jabatan_strings.split("\n")[1:])
        lokasi_string = text.split("Lokasi Formasi : ")[1].split("Jenis")[0]
        if len(lokasi_string.split("\n")) > 2:
            lokasi_back = " ".join(lokasi_string.split("\n")[1:])
        else:
            lokasi_back = lokasi_string.split(" - ")[1]

        return {
            "kode_jabatan": jabatan.split(" - ")[0],
            "jabatan": jabatan.split(" - ")[1],
            "kode_lokasi": lokasi_string.split(" - ")[0],
            "lokasi_formasi": lokasi_front+lokasi_back,
            "jenis_formasi": text.split("Jenis Formasi : ")[1].split("\n")[0],
            "pendidikan": pendidikan
        }
    else:
        return {}


def find_tms(df_):
    jumlah_formasi = df_.iloc[4, 1]
    lulus_akhir = df_.iloc[4, 10]
    jumlah_tms1 = df_.iloc[4, 8]
    sisa_formasi = jumlah_formasi - lulus_akhir

    tms1_terbaik = 0
    if sisa_formasi < jumlah_tms1:
        tms1_terbaik = sisa_formasi
    else:
        tms1_terbaik = jumlah_tms1
    return tms1_terbaik


def get_info_formasi_kosong_from_table(df_, jumlah_tms1):
    '''
    Fungsi untuk mengekstrak informasi dari tabel perorangan
    Input: df_ (dataframe tabel perorangan)
    Output:
        - dicitionary berisi informasi perorangan yang telah diekstrak
    '''
    jumlah_formasi = int(df_.iloc[4, 1])
    lulus_akhir = int(df_.iloc[4, 10])
    sisa_formasi = jumlah_formasi - lulus_akhir

    base_data = {
        "jumlah_peserta_skb": df_.iloc[4, 0],
        "jumlah_formasi": df_.iloc[4, 1],
        "jumlah_metode_skb": df_.iloc[4, 2],
        "peserta_total": df_.iloc[4, 3],
        "peserta_hadir": df_.iloc[4, 4],
        "peserta_th": df_.iloc[4, 5],
        "hasil_tl": df_.iloc[4, 6],
        "hasil_tms": df_.iloc[4, 7],
        "hasil_tms-1": df_.iloc[4, 8],
        "hasil_aps": df_.iloc[4, 9],
        "lulus_akhir": df_.iloc[4, 10],
        "sisa_formasi": sisa_formasi,
        "tms1_terbaik": jumlah_tms1
    }

    return {**base_data}


def get_info_from_table(df_, jumlah_tms1, page):
    '''
    Fungsi untuk mengekstrak informasi dari tabel perorangan
    Input: df_ (dataframe tabel perorangan)
    Output:
        - dicitionary berisi informasi perorangan yang telah diekstrak
    '''
   # keterangan_peserta = df_.iloc[7, 10]

   # if keterangan_peserta == "P/TMS-1":

    skd = df_.iloc[7:10, [1, 3]]
    skb = df_.iloc[13:, [1, 3, 4, 5, 6]]

    skd_dict = skd.set_index(1)[3].to_dict()
    skb_dict = skb.set_index(1)[3].to_dict()

    # bobot_skb = skb.set_index(1)[5]
    # bobot_skb.index = ["bobot_"+x for x in bobot_skb.index]
    # bobot_skb = bobot_skb.to_dict()

    # final_skb = skb.set_index(1)[6]
    # final_skb.index = ["final_"+x for x in final_skb.index]
    # final_skb = final_skb.to_dict()

    base_data = {
        "page": page,
        "no_peserta": df_.iloc[1, 1],
        "kode_pendidikan": df_.iloc[1, 2],
        "nama": df_.iloc[1, 3],
        "tanggal_lahir": df_.iloc[1, 8],
        "ipk": df_.iloc[1, 10],
        "keterangan": df_.iloc[7, 10],
        "total_skd": df_.iloc[7, 5],
        "total_skd_skala_100": df_.iloc[7, 7],
        "total_skd_dengan_bobot": df_.iloc[7, 8],
        "total_skd": df_.iloc[13, 7],
        "total_skb_dengan_bobot": df_.iloc[13, 8],
        "total_nilai_akhir": df_.iloc[7, 9],
        "tms1_terbaik": jumlah_tms1
    }

    return {**base_data, **skd_dict, **skb_dict}


def split_df(df_, tms1):
    '''
    Fungsi untuk split tabel perorangan. Kadang ada satu halaman dengan lebih dari satu tabel.
    Input: df_ (dataframe tabel perorangan)
    Output:
        - list berisi beberapa dataframe untuk tiap individu
    '''
    dfs = []
    header_indexes = list(df_[df_[1] == "No Peserta"].index)
    header_indexes.append(len(df_))
    count = tms1
    for i in range(len(header_indexes)-1):
        splitted_df = df_.iloc[header_indexes[i]: header_indexes[i+1], :]
        splitted_df.index = range(len(splitted_df))

        ket_peserta = splitted_df.iloc[7, 10]
        if ket_peserta == "P/TMS-1":
            if tms1 > 0:
                dfs.append(splitted_df)
                tms1 -= 1
                print("count : "+str(count))
            elif tms1 == 0:
                break
        else:
            tms1 = count

    return dfs, tms1


if __name__ == "__main__":
    # file_name = 'LampiranPasca.pdf'
    file_name = 'LAMPIRAN2_prasanggah.pdf'

    start_index = int(sys.argv[1])
    end_index = int(sys.argv[2])
    export_filename = file_name+".csv"
    pdf = pdfplumber.open(file_name)

    # start iterating
    result = []
    last_jabatan = {}

    start_time = dt.datetime.now()
    tms1_terbaik = 0
    is_formasi_kosong_found = False
    is_detail_found = False
    total_tms1 = 0

    for i in range(start_index, end_index):
        pg = pdf.pages[i]

        # jika halaman tsb ada info tentang lowongan, simpan
        current_jabatan = check_for_jabatan(pg)
        if current_jabatan != {}:
            last_jabatan = current_jabatan

        is_formasi_kosong_found, jumlah_tms1, formasi_kosong_df = check_formasi_kosong_page(
            pg)
        is_detail_found, detail_df = check_for_detail_tables(pg)

        # print("jumlah_tms1 : "+str(tms1_terbaik))

        if is_formasi_kosong_found:
            if jumlah_tms1 > 0:
                tms1_terbaik = jumlah_tms1
                # print("jumlah_tms1 : "+str(tms1_terbaik))
                print("page : "+str(i) +
                      " , formasi_kosong found, tms1_terbaik : "+str(tms1_terbaik))
                details = get_info_formasi_kosong_from_table(
                    formasi_kosong_df, tms1_terbaik)
                if current_jabatan == {}:
                    # kalo ada info lowongan di halaman yang sama, pakai info lowongan tsb
                    details.update(last_jabatan)
                else:
                    # kalo ga, pake info lowongan terakhir
                    details.update(current_jabatan)
                    last_jabatan = current_jabatan
                # result.append(details)
            else:
                tms1_terbaik = 0

        # print("page : "+str(i)+" , jumlah_tms1 : " +
        #       str(tms1_terbaik) + " detail_found "+str(is_detail_found))

        if is_detail_found:

            # print("page : "+str(i) +
            #       " , detailfound, tms1_terbaik : "+str(tms1_terbaik))

            # count_tms1 = tms1_terbaik
            # tms1_terbaik = 0
            if tms1_terbaik > 0:
                print("page detailfound : "+str(i) + " count_tms1 : " +
                      str(tms1_terbaik))
                splitted_df, count_tms1 = split_df(detail_df, tms1_terbaik)

                tms1_terbaik = count_tms1

                if len(splitted_df) != 0:
                    for df_ in splitted_df:
                        total_tms1 += 1
                        print("splitted_df page : "+str(i) +
                              " count_tms1 : "+str(tms1_terbaik))
                        # if i < count_tms1:
                        details = get_info_from_table(df_, tms1_terbaik, i+1)
                        if current_jabatan == {}:
                            # kalo ada info lowongan di halaman yang sama, pakai info lowongan tsb
                            details.update(last_jabatan)
                        else:
                            # kalo ga, pake info lowongan terakhir
                            details.update(current_jabatan)
                            last_jabatan = current_jabatan
                        result.append(details)
                        # i = i + 1

        # untuk logging
        if i % 100 == 99:
            curr_time = dt.datetime.now()
            print("Done for "+str(i), curr_time-start_time)
            start_time = dt.datetime.now()

    print("Total TMS-1 : "+str(total_tms1))
    res = pd.DataFrame(result)
    res.to_csv(export_filename)
