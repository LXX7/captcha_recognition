# -*- coding:utf-8 -*-
# @Author: 星星
# @Date:   2020-09-19 18:27:06
# @Last Modified time: 2020-09-19 18:33:46

from io import BytesIO
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
from chaojiying import Chaojiying
import time

# 注意：请改为自己的相关账号信息
PHONE = '***********'					# 微博账号
PASSWORD = '***********'				# 微博密码
CHAOJIYING_USERNAME = '**********'		# 超级鹰账号
CHAOJIYING_PASSWORD = '************'	# 超级鹰密码
CHAOJIYING_SOFT_ID = *****	            # 超级鹰软件ID
CHAOJIYING_KIND = ****	                # 图片识别类型

SUCCESS = False                         # 判断是否识别成功


class CrackWeibo():
    def __init__(self):
        self.url = 'https://passport.weibo.cn/signin/login'
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.phone = PHONE
        self.password = PASSWORD
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
        print("获取到验证码图片：", image)
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
        """点击验证码图片里的文字，提交后返回点击前后的URL变化"""
        for location in locations:
            print(location)
            ActionChains(self.browser).move_to_element_with_offset(self.get_weibo_element(), location[0], location[1]-30).click().perform()
            time.sleep(1)
        button = self.wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[3]/div[2]/div[1]/div/div/d'
                                                                             'iv[3]/a/div')))
        url1 = self.browser.current_url
        button.click()
        time.sleep(5)
        url2 = self.browser.current_url
        return url1, url2

    def validation_error(self, result, url1, url2):
        """根据点击后是否跳转页面，判断是否识别成功"""
        im_id = result['pic_id']
        if url1 == url2:
            print("识别失败", self.chaojiying.report_error(im_id))
            SUCCESS = False
        else:
            print("识别成功")
            SUCCESS = True
        return SUCCESS

    def close(self):
        """获取登陆后的页面信息，然后关闭浏览器"""
        print("获取的页面信息")
        print(self.browser.current_url)
        print(self.browser.get_cookies())
        print(self.browser.page_source)
        self.browser.close()

if __name__ == '__main__':

    crackweibo = CrackWeibo()

    # 登陆页面的操作,跳转到验证页面
    crackweibo.open()

    # 验证页面的操作
    crackweibo.get_weibo_button().click()								# 点击验证按钮
    # 不成功重新识别
    while not SUCCESS:
    	print('*'*50+'\n')
    	element = crackweibo.get_weibo_element()						# 获取验证码对象
    	top, bottom, left, right = crackweibo.get_position(element)		# 获取元素的位置
    	image = crackweibo.get_weibo_image(top, bottom, left, right)	# 获取验证码图片
    	captcha_result = crackweibo.picture_recognition(image)			# 传图片给超级鹰接口识别,返回json格式的识别结果
    	print("超级鹰识别结果：", captcha_result)
    	locations = crackweibo.get_word_points(captcha_result)			# 解析超级鹰的识别结果
    	# 根据识别结果，点击验证码
    	url1, url2 = crackweibo.touch_click_words(locations)			
    	#判断是否验证成功
    	SUCCESS = crackweibo.validation_error(captcha_result, url1, url2)
    crackweibo.close()
