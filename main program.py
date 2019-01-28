import mysql.connector
from PCPartPicker_API import pcpartpicker as pcpp
from bs4 import BeautifulSoup as BSoup
import urllib.request
from pprint import pprint as pp
import sqlite3 as sqlite
from requests_html import HTMLSession
session = HTMLSession()

pcpp.setRegion("au")

i = 0


print("Fetching CPUs")
print("")

cpu_info = pcpp.productLists.getProductList("cpu")

for cpu in cpu_info:
    i+=1

print("Fetched " + str(i) +" CPUs")
print("")

i = 0

print("Fetching motherboards")
print("")

motherboard_info = pcpp.productLists.getProductList("motherboard")

for motherboard in motherboard_info:
    i+=1

print("Fetched " + str(i) + " motherboards")
print("")

i = 0

print("Connecting to MySQL database (SQL)")
print("")

mydb = mysql.connector.connect(
  host="host",
  user="user",
  passwd="passwd",
  database="database"
)

print("Connected to MySQL database (SQL)")
print("")

mycursor = mydb.cursor()

#mycursor.execute("DROP TABLE IF EXISTS cpu")
#mycursor.execute("DROP TABLE IF EXISTS cpubench")
#mycursor.execute("DROP TABLE IF EXISTS motherboard")

mydb.commit()

mycursor.execute("CREATE TABLE IF NOT EXISTS cpu (num INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) UNIQUE, price VARCHAR(255), id VARCHAR(255) UNIQUE, mark VARCHAR(255), value VARCHAR(255), url VARCHAR(255), socket VARCHAR(255))")

print("Adding CPUs with price to cpu (SQL)")
print("")

for cpu in cpu_info:
    if not "(OEM/Tray)" in cpu["name"]:
        if cpu["price"] != "":
            i+=1
            tempname = cpu["name"]
            name = tempname.replace("Extreme Edition", "")
            sql = "INSERT IGNORE INTO cpu (name, price, id) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name), price=VALUES(price), id=VALUES(id)"
            val = (name, cpu['price'], cpu['id'])

            mycursor.execute(sql, val)

            mydb.commit()

print("Added " + str(i) + " CPUs with price to cpu (SQL)")
print("")

i = 0

mycursor.execute("CREATE TABLE IF NOT EXISTS motherboard (num INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) UNIQUE, price VARCHAR(255), id VARCHAR(255) UNIQUE, socket VARCHAR(255), ramslots VARCHAR(255), maxram VARCHAR(255), chipset VARCHAR(255), url VARCHAR(255))")

print("Adding motherboards with price to mobo (SQL)")
print("")

for motherboard in motherboard_info:
    if motherboard["price"] != "":
        i+=1
        sql = "INSERT IGNORE INTO motherboard (name, price, id, socket, ramslots, maxram) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name), price=VALUES(price), id=VALUES(id), socket=VALUES(socket), ramslots=VALUES(ramslots), maxram=VALUES(maxram)"
        val = (motherboard['name'], motherboard['price'], motherboard['id'], motherboard['socket'], motherboard['ram-slots'], motherboard['max-ram'])

        mycursor.execute(sql, val)

        mydb.commit()

print("Added " + str(i) + " motherboards with price to mobo (SQL)")
print("")

i = 0

mycursor.execute("CREATE TABLE IF NOT EXISTS cpubench (num INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) UNIQUE, mark VARCHAR(255), cpurank VARCHAR(255))")

print("Fetching CPU scores and adding to cpubench (SQL)")
print("")

BASE_URL = 'http://www.cpubenchmark.net/'
CPU_LIST_URL = BASE_URL + 'cpu_list.php'

def scrape_cpu_info(cpu_url):
    """not sure if this is useful. would like that "samples" data but the html is a mess"""
    with urllib.request.urlopen(cpu_url) as fcpuinfo:
        cpu_detail = BSoup(fcpuinfo)

        desc_table = cpu_detail.find('table', attrs={'class':'desc'})
        
        for row in desc_table('tr'):
            for td in row('td'):
                for tag in td(True):
                    text = tag.text.encode('utf8')
                    for pairs in text.split(b','):
                        kv = pairs.split(b':')
                        if len(kv) != 2:
                            continue
                        key, val = kv
                        key = key.strip()
                        val = val.strip()


def main():
    i = 0
    fields = [
            'name',
            'mark',
            'rank',
            'value',
            'price',
            ]
    data = []

    with urllib.request.urlopen(CPU_LIST_URL) as furl:
        cpu_list_soup = BSoup(furl, features="lxml")

        table = cpu_list_soup.find('table', attrs={'id':'cputable'})
        tbody = table.find('tbody')
        rows = tbody('tr')
        for cpurow in rows:
            tds = cpurow('td')
            if tds:
                row_texts = dict(zip(fields,
                    [td.text.encode('utf8') for td in tds]))
                oldname = str(row_texts['name'])
                oldmark = str(row_texts['mark'])
                oldrank = str(row_texts['rank'])
                tempname = oldname.replace("b'", "")
                tempname2 = tempname.replace("'", "")
                tempname3 = tempname2.replace("APU", "")
                tempname4 = tempname3.replace("Core2", "Core 2")
                tempname5 = tempname4.replace("Eight-Core", "")
                tempname6 = tempname5.replace("Six-Core", "")
                tempname7 = tempname6.replace("Quad-Core", "")
                tempname8 = tempname7.replace("Ryzen Threadripper", "Threadripper")
                tempmark = oldmark.replace("b'", "")
                mark = tempmark.replace("'", "")
                temprank = oldrank.replace("b'", "")
                rank = temprank.replace("'", "")
                sep = '@'
                name = tempname8.split(sep, 1)[0]
                cpurank = rank
                sql = "INSERT INTO cpubench (name, mark, cpurank) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name), mark=VALUES(mark), cpurank=VALUES(cpurank)"
                val = (name, mark, cpurank)

                mycursor.execute(sql, val)

                mydb.commit()
                     
                data.append(row_texts)

if __name__ == "__main__":
    main()

print("Fetched CPU scores and added to cpubench (SQL)")
print("")

i = 0

print("Joing CPU benchmarks to cpu (SQL)")
print("")

sql = ("update cpu join cpubench on UPPER(TRIM(cpu.name)) = UPPER(TRIM(cpubench.name)) set cpu.mark = cpubench.mark")

mycursor.execute(sql)

mydb.commit()

print("Joined CPU benchmarks to cpu (SQL)")
print("")

mycursor.execute("SELECT num, price, mark FROM cpu")

print("Calculating CPU value")
print("")

myresult = mycursor.fetchall()

for x in myresult:
  y = str(x)
  num, price, mark = y.split(',')
  num = num.replace("(", "")
  price = price.replace("'", "")
  price = price.replace(" ", "")
  price = price.replace("$", "")
  mark = mark.replace(")", "")
  mark = mark.replace("'", "")
  mark = mark.replace(" ", "")
  price = float(price)
  if mark != "None":
    i+=1
    mark = float(mark)
    value = mark/price
  else:
    value = 0
  value = round(value, 2)
  value = str(value)
  num = str(num)
  sql = "UPDATE cpu SET value = " + value + " WHERE num = " + num +";"
  mycursor.execute(sql)

  mydb.commit()

mydb.commit()

print("Calculated " + str(i) + " CPU values")
print("")

i = 0

print("Fetching CPU image and socket")
print("")

mycursor.execute("SELECT id, num, url, socket FROM cpu")

myresult = mycursor.fetchall()

for x in myresult:
  y = str(x)
  id, num, url, socket = y.split(',')
  id = id.replace(")", "")
  id = id.replace("(", "")
  id = id.replace("'", "")
  id = id.replace(",", "")
  id = id.replace(" ", "")
  num = num.replace(")", "")
  num = num.replace("(", "")
  num = num.replace("'", "")
  num = num.replace(",", "")
  num = num.replace(" ", "")
  url = url.replace(")", "")
  url = url.replace("(", "")
  url = url.replace("'", "")
  url = url.replace(",", "")
  url = url.replace(" ", "")
  socket = socket.replace(")", "")
  socket = socket.replace("(", "")
  socket = socket.replace("'", "")
  socket = socket.replace(",", "")
  socket = socket.replace(" ", "")

  if url == "None" or socket == "None" or socket == "64-bit":

    r = session.get('https://au.pcpartpicker.com/product/' + id)
    
    item = r.html.find('.item')[0]
    img = item.xpath('//img')[0]
    img.attrs['src']
    img = str(img.attrs['src'])

    sql = "UPDATE cpu SET url = %s WHERE num = %s;"
    url = img
    num = num
    print("New image for CPU number: " + num + " (SQL)")
    print("")
    input = (url, num)
    mycursor.execute(sql, input)

    mydb.commit()

    about = r.html.find('.specs.block')[0]
    about = about.find('h4')
    info = about[3].text
    temp, socket = info.split('\n')

    if socket == "64-bit":
          info = about[4].text
          temp, socket = info.split('\n')    

    sql = "UPDATE cpu SET socket = %s WHERE num = %s;"
    socket = socket
    num = num
    print("New socket type: " + socket + " for CPU number: " + num + " (SQL)")
    print("")
    input = (socket, num)
    mycursor.execute(sql, input)

    mydb.commit()

mydb.commit()

print("Fetched CPU images and sockets")
print("")

mycursor.execute("SELECT * FROM cpu")

myresult = mycursor.fetchall()

print("CPU table:")
print("")

for x in myresult:
  print(x)

print("")

mycursor.execute("SELECT * FROM motherboard")

myresult = mycursor.fetchall()

print("Motherboard table:")
print("")

for x in myresult:
  print(x)
