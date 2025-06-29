import os
import re
import time
import requests
import json
import pickle

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from markdownify import markdownify as md


def get_login_selectors(url):
    """
    根据URL返回对应网站的登录选择器

    参数:
        url (str): 网站URL

    返回:
        dict: 包含登录表单选择器的字典
    """
    # 提取域名
    domain = re.search(r"https?://([^/]+)", url)
    if domain:
        domain = domain.group(1)
    else:
        return None

    # 常见网站的登录选择器配置
    selectors = {
        # CSDN
        "csdn.net": {
            "login_url": "https://passport.csdn.net/login",
            "username_selector": (By.ID, "all"),
            "password_selector": (By.ID, "password-number"),
            "login_button_selector": (By.CSS_SELECTOR, ".btn-primary"),
            "success_check": lambda driver: "passport.csdn.net/login"
            not in driver.current_url,
        },
        # 博客园
        "cnblogs.com": {
            "login_url": "https://account.cnblogs.com/signin",
            "username_selector": (By.ID, "LoginName"),
            "password_selector": (By.ID, "Password"),
            "login_button_selector": (By.ID, "submitBtn"),
            "success_check": lambda driver: "account.cnblogs.com/signin"
            not in driver.current_url,
        },
        # 掘金
        "juejin.cn": {
            "login_url": "https://juejin.cn/login",
            "username_selector": (By.CSS_SELECTOR, 'input[name="loginPhoneOrEmail"]'),
            "password_selector": (By.CSS_SELECTOR, 'input[name="loginPassword"]'),
            "login_button_selector": (By.CSS_SELECTOR, ".btn-login"),
            "success_check": lambda driver: "juejin.cn/login" not in driver.current_url,
        },
        # 知乎
        "zhihu.com": {
            "login_url": "https://www.zhihu.com/signin",
            "username_selector": (By.NAME, "username"),
            "password_selector": (By.NAME, "password"),
            "login_button_selector": (By.CSS_SELECTOR, 'button[type="submit"]'),
            "success_check": lambda driver: "www.zhihu.com/signin"
            not in driver.current_url,
        },
        # GitHub
        "github.com": {
            "login_url": "https://github.com/login",
            "username_selector": (By.ID, "login_field"),
            "password_selector": (By.ID, "password"),
            "login_button_selector": (By.CSS_SELECTOR, 'input[type="submit"]'),
            "success_check": lambda driver: "github.com/login"
            not in driver.current_url,
        },
        # 简书
        "jianshu.com": {
            "login_url": "https://www.jianshu.com/sign_in",
            "username_selector": (By.ID, "session_email_or_mobile_number"),
            "password_selector": (By.ID, "session_password"),
            "login_button_selector": (By.CSS_SELECTOR, 'input[type="submit"]'),
            "success_check": lambda driver: "www.jianshu.com/sign_in"
            not in driver.current_url,
        },
        # 思否
        "segmentfault.com": {
            "login_url": "https://segmentfault.com/login",
            "username_selector": (By.CSS_SELECTOR, 'input[name="username"]'),
            "password_selector": (By.CSS_SELECTOR, 'input[name="password"]'),
            "login_button_selector": (By.CSS_SELECTOR, 'button[type="submit"]'),
            "success_check": lambda driver: "segmentfault.com/login"
            not in driver.current_url,
        },
        # 牛客网
        "nowcoder.com": {
            "login_url": "https://www.nowcoder.com/login",
            "username_selector": (By.CSS_SELECTOR, 'input[name="email"]'),
            "password_selector": (By.CSS_SELECTOR, 'input[name="password"]'),
            "login_button_selector": (By.CSS_SELECTOR, ".btn-login"),
            "success_check": lambda driver: "www.nowcoder.com/login"
            not in driver.current_url,
        },
        # LeetCode中文
        "leetcode.cn": {
            "login_url": "https://leetcode.cn/accounts/login/",
            "username_selector": (By.ID, "id_login"),
            "password_selector": (By.ID, "id_password"),
            "login_button_selector": (By.CSS_SELECTOR, 'button[type="submit"]'),
            "success_check": lambda driver: "leetcode.cn/accounts/login"
            not in driver.current_url,
        },
    }

    # 查找匹配的域名
    for site_domain, site_selectors in selectors.items():
        if site_domain in domain:
            return site_selectors

    # 如果没有预定义的选择器，返回None
    return None


def login_website(url, username=None, password=None, cookies_path=None):
    """
    登录网站并保存cookies，或者加载已保存的cookies

    参数:
        url (str): 登录页面的URL
        username (str): 用户名
        password (str): 密码
        cookies_path (str): cookies保存路径

    返回:
        webdriver: 已登录的WebDriver实例
    """
    # 设置 selenium webdriver
    chrome_options = Options()
    # 如果不需要看到浏览器界面，可以取消下面这行的注释
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    # 添加用户数据目录以保存登录状态
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(script_dir, "chrome_user_data")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=chrome_options
    )

    # 如果有保存的cookies，尝试加载
    if cookies_path and os.path.exists(cookies_path):
        driver.get(url)  # 先访问网站
        try:
            cookies = pickle.load(open(cookies_path, "rb"))
            for cookie in cookies:
                # 有些cookie可能包含无法序列化的对象，需要处理异常
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    continue
            print("已加载保存的cookies")
            driver.refresh()  # 刷新页面应用cookies
            return driver
        except Exception as e:
            print(f"加载cookies失败: {e}")

    # 获取网站的登录选择器
    selectors = get_login_selectors(url)

    # 如果没有cookies或加载失败，且提供了用户名和密码，则进行登录
    if username and password and selectors:
        # 使用网站特定的登录URL
        login_url = selectors.get("login_url", url)
        driver.get(login_url)

        # 等待登录页面加载并进行登录
        try:
            # 使用网站特定的选择器
            username_selector = selectors["username_selector"]
            password_selector = selectors["password_selector"]
            login_button_selector = selectors["login_button_selector"]

            # 等待用户名输入框出现
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(username_selector)
            )

            # 找到密码输入框和登录按钮
            password_input = driver.find_element(*password_selector)
            login_button = driver.find_element(*login_button_selector)

            # 输入用户名和密码
            username_input.send_keys(username)
            password_input.send_keys(password)
            login_button.click()

            # 等待登录成功
            success_check = selectors.get("success_check", lambda d: True)
            WebDriverWait(driver, 10).until(lambda d: success_check(d))

            print("登录成功")

            # 保存cookies
            if cookies_path:
                os.makedirs(os.path.dirname(cookies_path), exist_ok=True)
                pickle.dump(driver.get_cookies(), open(cookies_path, "wb"))
                print(f"Cookies已保存到: {cookies_path}")

        except Exception as e:
            print(f"自动登录失败: {e}")
            print("切换到手动登录模式...")
            # 如果自动登录失败，切换到手动登录
            driver.get(url)
            input("请在浏览器中手动登录，然后按Enter继续...")

            # 保存手动登录的cookies
            if cookies_path:
                os.makedirs(os.path.dirname(cookies_path), exist_ok=True)
                pickle.dump(driver.get_cookies(), open(cookies_path, "wb"))
                print(f"手动登录的Cookies已保存到: {cookies_path}")
    else:
        # 如果没有提供用户名密码或没有找到网站的选择器，使用手动登录
        driver.get(url)
        input("请在浏览器中手动登录，然后按Enter继续...")

        # 保存手动登录的cookies
        if cookies_path:
            os.makedirs(os.path.dirname(cookies_path), exist_ok=True)
            pickle.dump(driver.get_cookies(), open(cookies_path, "wb"))
            print(f"手动登录的Cookies已保存到: {cookies_path}")

    return driver


def download_images_from_md(
    url, use_login=False, username=None, password=None, cookies_path=None
):
    """
    从给定的URL下载Markdown内容和所有引用的图片。

    参数:
        url (str): 目标页面的URL。
    """
    try:
        # 根据是否需要登录选择不同的方式获取页面
        if use_login:
            # 使用登录函数获取已登录的driver
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if not cookies_path and username and password:
                cookies_path = os.path.join(script_dir, "saved_cookies.pkl")

            driver = login_website(url, username, password, cookies_path)
        else:
            # 不需要登录，使用原来的方式
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=chrome_options,
            )
            driver.get(url)

        # 等待页面加载完成
        try:
            WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.TAG_NAME, "pre")),
                    EC.presence_of_element_located((By.CLASS_NAME, "markdown-body")),
                )
            )
        except Exception as e:
            print(f"等待页面元素超时: {e}")

        # 获取页面源代码和标题
        html_content = driver.page_source
        page_title = driver.title
        driver.quit()

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # 清理标题作为安全的文件名
        safe_title = (
            re.sub(r'[\\/*?"<>|]', "", page_title).strip() or f"page-{int(time.time())}"
        )

        # 查找内容容器
        content_container = soup.find("div", class_="markdown-body")
        is_html_content = True
        if not content_container:
            content_container = soup.find("pre")
            is_html_content = False

        if not content_container:
            content_container = soup.body
            is_html_content = True

        if not content_container:
            print("错误：无法找到页面的主要内容。")
            return

        # 提取Markdown内容
        if is_html_content:
            original_md_content = md(str(content_container), heading_style="ATX")
        else:
            original_md_content = content_container.get_text()

        # 从Markdown内容中提取图片链接
        img_urls = re.findall(r"!\[.*?\]\((.*?)\)", original_md_content)

        # 创建保存目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(script_dir, safe_title)
        os.makedirs(folder_path, exist_ok=True)
        print(f"文件将保存到: {folder_path}")

        # 下载图片并替换链接
        modified_md_content = original_md_content
        for i, img_url in enumerate(img_urls):
            if not img_url:
                continue

            full_img_url = urljoin(url, img_url)
            try:
                print(f"正在下载: {full_img_url}")
                response = requests.get(full_img_url, stream=True)
                response.raise_for_status()

                file_ext = os.path.splitext(img_url.split("?")[-1])[-1] or ".jpg"
                if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                    file_ext = ".jpg"

                local_file_name = f"{i+1:02d}{file_ext}"
                local_file_path = os.path.join(folder_path, local_file_name)

                with open(local_file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"已下载 {local_file_name}")

                # 替换原始URL为本地相对路径
                modified_md_content = modified_md_content.replace(
                    img_url, f"/img/blog/blog_date_to_replace/{local_file_name}"
                )

            except requests.exceptions.RequestException as e:
                print(f"下载失败 {full_img_url}: {e}")

        # 保存修改后的Markdown文件
        md_file_path = os.path.join(folder_path, f"{safe_title}.md")
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(modified_md_content)
        print(f"Markdown 文件已保存到: {md_file_path}")

        print("处理完成。")

    except Exception as e:
        print(f"发生意外错误: {e}")


def save_config(config, config_path):
    """
    保存配置到文件

    参数:
        config (dict): 配置字典
        config_path (str): 配置文件路径
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("配置已保存")
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


def load_config(config_path, default_config=None):
    """
    从文件加载配置

    参数:
        config_path (str): 配置文件路径
        default_config (dict): 默认配置

    返回:
        dict: 加载的配置
    """
    config = default_config or {}

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
            print("已加载配置文件")
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    return config


if __name__ == "__main__":
    # 配置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "spider_config.json")
    cookies_dir = os.path.join(script_dir, "cookies")
    os.makedirs(cookies_dir, exist_ok=True)

    # 默认配置
    default_config = {
        "use_login": False,
        "username": "",
        "password": "",
        "cookies_path": os.path.join(cookies_dir, "default_cookies.pkl"),
        "site_specific_cookies": True,  # 是否为每个网站使用特定的cookies文件
    }

    # 加载配置
    config = load_config(config_path, default_config)

    # 询问是否需要修改配置
    modify_config = input("是否需要修改配置？(y/n, 默认n): ").strip().lower()
    if modify_config == "y":
        use_login = (
            input(
                f"是否需要登录？(y/n, 当前: {'是' if config['use_login'] else '否'}): "
            )
            .strip()
            .lower()
        )
        if use_login:
            config["use_login"] = use_login == "y"

        if config["use_login"]:
            username = input(f"请输入用户名 (当前: {config['username']}): ").strip()
            if username:
                config["username"] = username

            password = input(
                f"请输入密码 (当前: {'*'*len(config['password']) if config['password'] else '空'}): "
            ).strip()
            if password:
                config["password"] = password

            site_specific = (
                input(
                    f"是否为每个网站使用特定的cookies文件？(y/n, 当前: {'是' if config['site_specific_cookies'] else '否'}): "
                )
                .strip()
                .lower()
            )
            if site_specific:
                config["site_specific_cookies"] = site_specific == "y"

        # 保存配置
        save_config(config, config_path)

    while True:
        target_url = input("请输入Markdown文件的URL (输入 'q' 退出): ")
        if target_url.lower() in ["q", "quit", "exit"]:
            break

        # 简单的URL验证
        if not target_url.strip().startswith(("http://", "https://")):
            print("无效的URL。请输入以 'http://' 或 'https://' 开始的有效URL。")
            continue

        # 处理URL
        target_url = target_url.strip()

        # 如果启用了站点特定cookies，为当前网站生成特定的cookies路径
        cookies_path = config["cookies_path"]
        if config["use_login"] and config["site_specific_cookies"]:
            # 从URL提取域名作为cookies文件名
            domain_match = re.search(r"https?://([^/]+)", target_url)
            if domain_match:
                domain = domain_match.group(1).replace(".", "_")
                cookies_path = os.path.join(cookies_dir, f"{domain}_cookies.pkl")

        # 使用配置调用下载函数
        download_images_from_md(
            target_url,
            use_login=config["use_login"],
            username=config["username"],
            password=config["password"],
            cookies_path=cookies_path,
        )
