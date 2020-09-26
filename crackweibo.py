# -*- coding:utf-8 -*-
# @Author: 星星
# @Date:   2020-09-19 18:27:06
# @Last Modified time: 2020-09-27 07:33:28

from io import BytesIO
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
from chaojiying import Chaojiying
import time
from selenium.webdriver.chrome.options import Options


# 注意：请改为自己的相关账号信息
CHAOJIYING_USERNAME = '**********'      # 超级鹰账号
CHAOJIYING_PASSWORD = '************'    # 超级鹰密码
CHAOJIYING_SOFT_ID = *****              # 超级鹰软件ID
CHAOJIYING_KIND = ****                  # 图片识别类型

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

class CrackWeibo():
    def __init__(self, username, password):

        self.url = 'https://passport.weibo.cn/signin/login'
        self.browser = webdriver.Chrome(chrome_options=chrome_options)
        self.wait = WebDriverWait(self.browser, 20)
        self.phone = username
        self.password = password
        self.chaojiying = Chaojiying(CHAOJIYING_USERNAME, CHAOJIYING_PASSWORD, CHAOJIYING_SOFT_ID)

    def open(self):
        """打开网页，输入用户名和密码,点击登陆,切换到验证码的页面"""
        self.browser.get(self.url)
        phone = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="loginName"]')))
        password = self.wait.until(EC.visibility_of_element_located((By.ID, 'loginPassword')))
        phone.send_keys(self.phone)
        password.send_keys(self.password)
        button = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="loginAction"]')))
        button.click()

    def password_error(self):
        """
        判断是否密码错误
        :return:
        """
        try:
            return WebDriverWait(self.browser, 5).until(
                EC.text_to_be_present_in_element((By.ID, 'errorMsg'), '用户名或密码错误'))
        except TimeoutException:
            return False

    def login_successfully(self):
        """
        判断是否登录成功
        :return:
        """
        try:
            return bool(
                WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[1]/div[1]'))))
        except TimeoutException:
            return False

    def get_weibo_button(self):
        """获取验证按钮"""
        button = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="embed-captcha"]/div/div[2]/div[1'
                                                                             ']/div[3]/span[1]')))
        return button

    def get_weibo_element(self):
        """获取验证图片对象"""
        
        element = self.wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[3]/div[2]/div[1]')))
        return element

    def get_position(self, element):
        """获取验证图片对象位置"""
        location = element.location
        size = element.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return top, bottom, left, right

    def get_weibo_image(self, top, bottom, left, right):
        """获取验证码图片"""
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot)).resize((1200, 764))
        captcha = screenshot.crop((left, top+30, right, bottom+30))
        return captcha

    def picture_recognition(self, image):
        """图片的文字位置，用超级鹰识别，返回识别的json格式"""
        bytes_array = BytesIO()
        image.save(bytes_array, format='PNG')
        result = self.chaojiying.post_pic(bytes_array.getvalue(), CHAOJIYING_KIND)
        return result

    def get_word_points(self, captcha_result):
        """解析文字的识别结果"""
        groups = captcha_result.get('pic_str').split('|')
        locations = [[int(number) for number in group.split(',')] for group in groups]
        return locations

    def touch_click_words(self, locations):
        """点击验证码图片里的文字"""
        for location in locations:
            ActionChains(self.browser).move_to_element_with_offset(self.get_weibo_element(), location[0], location[1]-30).click().perform()
            time.sleep(1)
        button = self.wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[3]/div[2]/div[1]/div/div/d'
                                                                             'iv[3]/a/div')))
        button.click()

    def validation_error(self, result):
        """调用超级鹰识别失败接口返回积分"""
        im_id = result['pic_id']
        self.chaojiying.report_error(im_id)
    

    def get_cookies(self):
        """获取登陆后的页面信息，然后关闭浏览器"""
        return self.browser.get_cookies()
        self.browser.close()

    def main(self):
        """破解入口"""
        SUCCESS = False
        # 登陆页面的操作,跳转到验证页面
        self.open()
        if self.password_error():
            return {
                'status': 2,
                'content': '用户名或密码错误'
            }        
        else:
            # 验证页面的操作
            self.get_weibo_button().click()                             # 点击验证按钮
            # 如果不需要验证码直接登录成功
            if self.login_successfully():
                cookies = self.get_cookies()
                return {
                    'status': 1,
                    'content': cookies
                }
            else:
                while not SUCCESS:
                    print("开始识别验证码")
                    element = self.get_weibo_element()                      # 获取验证码对象
                    print("开始获取元素位置")
                    top, bottom, left, right = self.get_position(element)       # 获取元素的位置
                    print("根据元素位置",top, bottom, left, right, '获取验证码图片')
                    image = self.get_weibo_image(top, bottom, left, right)  # 获取验证码图片
                    print("超级鹰开始识别图片")
                    captcha_result = self.picture_recognition(image)            # 传图片给超级鹰接口识别,返回json格式的识别结果
                    print("识别结果：", captcha_result)
                    locations = self.get_word_points(captcha_result)            # 解析超级鹰的识别结果
                    print("解析识别结果为坐标参数：", locations, "\n根据坐标开始点击验证码图片")
                    # 根据识别结果，点击验证码
                    self.touch_click_words(locations)
                    #判断是否验证成功
                    SUCCESS = self.login_successfully()
                    if SUCCESS:
                        cookies = self.get_cookies()
                        return {
                            'status': 3,
                            'content': cookies
                        }
                    else:
                        self.validation_error(captcha_result)
                        print("识别失败,重新开始\n")

if __name__ == '__main__':
    result = WeiboCookies('微博账号', '密码').main()
    print(result)
