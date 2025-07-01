# 网页内容爬虫工具

这个工具可以从网页下载Markdown内容和相关图片，并支持需要登录的网站。

## 功能特点

- 支持从网页下载Markdown内容
- 自动下载Markdown中引用的图片
- 支持替换图片链接为本地相对路径
- 支持需要登录的网站（自动或手动登录）
- 支持保存和加载cookies
- 支持为不同网站使用不同的cookies文件
- 内置多个常见网站的登录选择器配置

## 使用方法

1. 运行脚本：

   ```bash
   python spider.py
   ```

2. 首次运行时，会询问是否需要修改配置：
   - 是否需要登录
   - 用户名和密码（如果需要登录）
   - 是否为每个网站使用特定的cookies文件

3. 输入要下载的网页URL

4. 脚本会自动下载内容并保存到本地

## 配置文件

配置保存在`spider_config.json`文件中，包含以下字段：

```json
{
    "use_login": true,
    "username": "",
    "password": "",
    "cookies_path": "cookies/default_cookies.pkl",
    "site_specific_cookies": true
}
```

- `use_login`: 是否需要登录
- `username`: 登录用户名
- `password`: 登录密码
- `cookies_path`: cookies保存路径
- `site_specific_cookies`: 是否为每个网站使用特定的cookies文件

## 支持的网站

工具内置了以下网站的登录选择器配置：

- CSDN (csdn.net)
- 博客园 (cnblogs.com)
- 掘金 (juejin.cn)
- 知乎 (zhihu.com)
- GitHub (github.com)
- 简书 (jianshu.com)
- 思否 (segmentfault.com)
- 牛客网 (nowcoder.com)
- LeetCode中文 (leetcode.cn)

对于未内置配置的网站，工具会尝试自动检测登录元素，或提示用户手动登录。

## 注意事项

- 首次登录网站时，可能需要手动处理验证码
- 登录成功后，cookies会被保存，下次访问同一网站时可以自动使用
- 如果遇到登录问题，可以尝试删除cookies文件重新登录
