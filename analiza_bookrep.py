import requests
import re
import os
import csv
import time
L = 30000
###############################################################################
# Najprej definirajmo nekaj pomožnih orodij za pridobivanje podatkov s spleta.
###############################################################################

# definirajte URL glavne strani z oglasi
knjige_url1 = "https://www.bookdepository.com/category/3391/Teen-Young-Adult?page="

# mapa, v katero bomo shranili podatke
knjige_dir = "all_teen_and_young_adult"
# ime datoteke v katero bomo shranili glavno stran
frontpage_filename = "knjige"
# ime CSV datoteke v katero bomo shranili podatke
csv_filename = "knjige"

def download_url_to_string(url):
    """Funkcija kot argument sprejme niz in poskusi vrniti vsebino te spletne
    strani kot niz. V primeru, da med izvajanje pride do napake vrne None.
    """
    try:
        # del kode, ki morda sproži napako
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        # koda, ki se izvede pri napaki
        # dovolj je če izpišemo opozorilo in prekinemo izvajanje funkcije
        print("Napaka pri povezovanju do:", url)
        return None
    # nadaljujemo s kodo če ni prišlo do napake
    if r.status_code == requests.codes.ok:
        return r.text
    else:
        print("Napaka pri prenosu strani:", url)
        return None

def save_string_to_file(text, directory, filename):
    """Funkcija zapiše vrednost parametra "text" v novo ustvarjeno datoteko
    locirano v "directory"/"filename", ali povozi obstoječo. V primeru, da je
    niz "directory" prazen datoteko ustvari v trenutni mapi.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(text)
    return None

# Definirajte funkcijo, ki prenese glavno stran in jo shrani v datoteko.
#30 knjig na stran
def save_frontpage(directory, d):
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz"""
    i = 1
    while i < d:
        knjige_url = knjige_url1 + str(i)
        print(knjige_url)
        text = download_url_to_string(knjige_url)
        save_string_to_file(text, directory, f"knjige{str(i)}.html")
        i += 1
    return None

###############################################################################
# Po pridobitvi podatkov jih želimo obdelati.
###############################################################################

def read_links_to_adds(dir, filename):
    dat = read_file_to_string(dir, filename)
    rx  = re.compile(r"<a.*href=(\"/povezava_knjige.*)>.*</a>")
    ads = re.findall(rx, dat)
    return ads

def open_add_link_return_info(url):
    ret = {"kategorije":[]}
    url = "https://www.bookdepository.com/" + url[1:]
    fl = download_url_to_string(url)
    #print(fl)
    #vem da ni prou sam drgac ne dela nevem zakaj
    rx = re.compile(r"<h1 itemprop=\"name\">(?P<naslov>.*)</h1|<span itemprop=\"author\".*itemscope=\"(?P<avtor>.*)\">|<a href=\"/category.*\" (.*|>)\n *(?P<kategorije>.*)</a>|<div class=\"price item-price-wrap\">\n *<span class=\"sale-price\">(?P<cena>.*) €</span>|<span itemprop=\"ratingValue\">\n *(?P<ocena>.*)</span>|<label>Language</label>\n *<span>\n *(?P<jezik>.*)</span>|<meta itemprop=\"ratingCount\" content=\"(?P<stevilo_glasov>.*)\"/>|<span itemprop=\"datePublished\">\d\d (?P<mesec>\w\w\w) (?P<datum>\d\d\d\d)</span>|<span itemprop=\"numberOfPages\">(?P<stevilo_strani>.*) pages\n</span>|<span itemprop=\"publisher\" .* itemscope=\"(?P<zaloznik>.*)\">|<span>\n *(?:\")?(?P<lestvica>\d.*)(?:\")?</span|<label>For ages</label>\n *<span>(?P<starost>.*)</span|Publication City/Country</label>\n *<span>\n *.*, (|\w\w, )(?P<drzava>.*)</span")
    l = [m.groupdict() for m in rx.finditer(str(fl))]
    for listing in l:
        for key, val in listing.items():
            if val != None:
                if key == "kategorije":
                    ret[key].append(val)
                    
                else:    
                    ret[key] = val            
    return ret


def read_file_to_string(directory, filename):
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz"""
    path = os.path.join(directory, filename)
    with open(path, 'r', encoding='utf-8') as file_in:
        return file_in.read()


def make_big_csv_from_small_csv(dir, fn):
    c = 0
    keys = []
    os.makedirs(dir, exist_ok=True)
    path = os.path.join(dir, fn)
    with open(path, "w", encoding="utf-8") as csv_file:
        for file in os.listdir(dir):
            if file.endswith(".csv") and file != "koncni.csv":
                with open(dir + "\\" + file, "r", encoding="utf-8") as file:
                    dic = read_csv_return_dict(file)
                for key, val in dic.items():
                    if key not in keys:
                        keys.append(key) #ja vem ful neucinkovito loh bi naredu to ze prej ampak ohwell
        writer = csv.DictWriter(csv_file, keys)
        writer.writeheader()
        for file in os.listdir(dir):
            ime = file
            c += 1
            if file.endswith(".csv"):
                with open(dir + "\\" + file, "r", encoding="utf-8") as file:
                    dic = read_csv_return_dict(file)
                    writer.writerow(dic)
                    print(f"krneki_{c}")
            if ime != "koncni.csv":
                os.remove(dir + "//" + ime)

def read_csv_return_dict(myfile):
    dic = {}
    for row in myfile:
        if row == "\n":
            continue
        row = row.replace("&#039;", "\'")
        row = row.replace("&amp;", "&")
        row = row.replace("\"", "")
        row = row.replace("\n", "")
        row = row.split("#")
        dic[row[0]] = row[1]
    return dic
                
###############################################################################
# Obdelane podatke želimo sedaj shraniti.
###############################################################################


def make_csv(dict, dir, filename):
    os.makedirs(dir, exist_ok=True)
    path = os.path.join(dir, filename)
    with open(path, "w", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter="#")
        for key, val in dict.items():
            writer.writerow([key, val])
    return None




def main(redownload=True, reparse=True):
    # save_frontpage(knjige_dir, 400)
    # print("konec lonec")
    # for j in range(1, 334): #shrani knjige iz strani na poseben html
    #     dat = read_file_to_string(knjige_dir, f"knjige{j}.html")
    #     rx = re.compile(r"<div class=\"item-img\">\n *<a href=\"(.{0,100}ref=grid-view)\">\n *")
    #     links_to_info = re.findall(rx, dat)
    #     for k, link in enumerate(links_to_info):
    #         info = open_add_link_return_info(link)
    #         make_csv(info, knjige_dir, f"retc_{j}_{k}.csv")
    #         print(j, k)

    make_big_csv_from_small_csv(knjige_dir, "koncni.csv")


# def read_links_to_adds(dir, filename):
#     dat = read_file_to_string(dir, filename)
#     rx  = re.compile(r"<a.*href=(\"/povezava_knjige.*)>.*</a>")
#     ads = re.findall(rx, dat)
#     return ads


if __name__ == '__main__':
    main()


