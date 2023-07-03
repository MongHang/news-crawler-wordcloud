import jieba as jieba
from io import StringIO
from opencc import OpenCC
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import pandas as pd
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
import string
import requests
import re
tqdm.pandas()

# https://blog.csdn.net/u011519550/article/details/106130366
# 用高度變化檢查是否滾動到底
def checkBottom():
    temp_height = 0
    while True:
        driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        time.sleep(0.5)
        check_height = driver.execute_script("return document.documentElement.scrollTop || window.pageYOffset || document.body.scrollTop;")
        if check_height == temp_height:
            print(f"height: {check_height}")
            break
        else:
            temp_height = check_height
            # print(f"height: {check_height}")

url = "https://tw.news.yahoo.com/"

opt = Options()
opt.add_argument('--headless') # 啟動無頭模式
opt.add_argument('--disable-gpu') # 關gpu，省電

driver = webdriver.Chrome(options=opt)
driver.get(url)

checkBottom()

soup = BeautifulSoup(driver.page_source, "html.parser")

driver.quit()

datas = []

# class="D(ib) Ov(h) Whs(nw) C($c-fuji-grey-l) C($c-fuji-blue-1-c):h Td(n) Fz(16px) Tov(e) Fw(700)"
# class="C($c-fuji-grey-l) Fw(b) Fz(20px) Lh(23px) LineClamp(2,46px) Fz(17px)--sm1024 Lh(19px)--sm1024 LineClamp(2,38px)--sm1024 mega-item-header-link Td(n) C(#0078ff):h C(#000) LineClamp(2,46px) LineClamp(2,38px)--sm1024 not-isInStreamVideoEnabled"

classes = [
    "D(ib) Ov(h) Whs(nw) C($c-fuji-grey-l) C($c-fuji-blue-1-c):h Td(n) Fz(16px) Tov(e) Fw(700)",
    "C($c-fuji-grey-l) Fw(b) Fz(20px) Lh(23px) LineClamp(2,46px) Fz(17px)--sm1024 Lh(19px)--sm1024 LineClamp(2,38px)--sm1024 mega-item-header-link Td(n) C(#0078ff):h C(#000) LineClamp(2,46px) LineClamp(2,38px)--sm1024 not-isInStreamVideoEnabled"
]

for c in classes:
    ls = soup.find_all("a", class_=c)
    passTitle = 0
    for l in ls:
        if l.text in datas:
            print(f"<pass>標題: {l.text}")
            passTitle += 1
            continue
        else:
            print(f" <new>標題: {l.text}")
            datas.append(l.text)
    print(len(datas))
    print(passTitle)

newsdf = pd.DataFrame({"標題": datas})

# 載入2套stopword辭典，增加切片精準?
url = r'https://raw.githubusercontent.com/fxsjy/jieba/master/extra_dict/dict.txt.big'
response = requests.get(url)
with open ('dict.txt.big', 'w', encoding='utf-8') as f:
    f.write(response.text)

url = r'https://raw.githubusercontent.com/goto456/stopwords/master/baidu_stopwords.txt'
response = requests.get(url)
# StringIO模組主要用於在記憶體緩衝區中讀寫資料，讀寫較快(短時間的重複利用，不用存很久的資料可使用)
io_obj = StringIO(response.text)
stopwords = io_obj.getvalue().split('\n')

def _jieba_cut_words(s):
    cut_words = jieba.cut(s, cut_all=False)
    result = []
    for word in cut_words:
        word = word.strip()# len(word) > 1是為了篩選有意義的詞彙
        if len(word) > 1 and word not in stopwords:
            result += [word]
    return ' '.join(result)

def _cc_transform(x):
    return cc.convert(x)

def _remove_punctuation(x):
    removed = re.sub(pattern, ' ', x)
    return re.sub('[^\w\s]', ' ', removed)
def cleansing(data):
    removed = _remove_punctuation(data)
    converted = _cc_transform(removed)
    cut_words = _jieba_cut_words(converted)
    return cut_words

dict_path = 'dict.txt.big'

jieba.set_dictionary(dict_path) # 在0.28之前不能指定主辭典的路徑，有了延遲加載機制後，可以改變主辭典的路徑
jieba.initialize() # 手動初始化(可選)

cc = OpenCC('s2twp') # s2twp: opencc繁簡轉換

pattern = f"[{string.punctuation}]"
pattern = pattern.replace('.', '').replace('-', '')

stopwords = [cc.convert(word) for word in stopwords]

newsdf['bow'] = newsdf["標題"].progress_apply(cleansing)

##################### 測試功能 ##################################
# frequencies = WordCloud().process_text(' '.join(newsdf.bow))
# frequencies
###############################################################

# url = r'https://raw.githubusercontent.com/g0v/moedict.tw/master/SourceHanSansTW-Normal.ttf'

# response = requests.get(url)
# with open(r'SourceHanSansTW-Normal.ttf', 'wb') as f:
#     f.write(response.content)

mask = plt.imread("cat.jpg")
image_colors = ImageColorGenerator(mask) # 擷取圖片的顏色分布
plt.figure(figsize=(20, 20))
wc = WordCloud(
    stopwords=STOPWORDS,
    font_path='kaiu.ttf',
    max_words=2560,
    width=1920,
    height=1080,
    mask=mask,
    background_color="white",
    # colormap="Set1", # 顏色參數: Matplotlib colormap
    color_func=image_colors # 根據圖片顏色分布上色
)

wc = wc.generate(' '.join(newsdf.bow))
plt.imshow(wc, interpolation='bilinear')

wc.to_file('yahoo焦點CW.png')