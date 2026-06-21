# BossPilot Chrome 插件

这是 BossPilot 的 Chrome Extension MVP，用于从 Boss 直聘网页版读取用户当前可见页面文本。插件支持单次采集，也支持用户主动开启的求职会话监控模式。

## 本地开发

默认发送地址在 `popup.js` 顶部：

```js
const BOSSPILOT_URL = "http://localhost:8501";
```

部署后可改为：

```js
const BOSSPILOT_URL = "https://bosspilot-yij7.streamlit.app";
```

## 安装方法

1. 打开 Chrome 扩展程序页面：`chrome://extensions/`
2. 打开“开发者模式”
3. 点击“加载已解压的扩展程序”
4. 选择项目中的 `browser_extension` 文件夹
5. 打开 Boss 直聘网页版岗位详情页
6. 点击浏览器工具栏中的 BossPilot 插件按钮
7. 点击“发送到 BossPilot 分析”
8. 插件会打开 BossPilot 页面并自动导入、分析和保存岗位

## 求职会话监控模式

会话监控模式用于连续浏览多个 Boss 岗位后统一上传。

使用步骤：

1. 在项目根目录启动本地接收器：

```bash
python local_receiver.py
```

2. 启动 BossPilot：

```bash
streamlit run app.py
```

3. 打开 Boss 直聘网页版。
4. 点击插件“开始监控”。
5. 正常浏览岗位列表、岗位详情、公司页或聊天页。
6. 点击插件“查看已采集数量”可查看当前采集页面数和岗位数。
7. 点击“结束并上传”，插件会把本次会话发送到：

```js
const BOSSPILOT_RECEIVER_URL = "http://127.0.0.1:8765/api/import-session";
```

8. 回到 BossPilot 页面，在“导入浏览器监控会话”中选择会话并点击“导入并分析本次会话”。
9. 如需删除插件本地会话缓存，点击“清空本次记录”。

## 说明

- 插件只读取用户当前打开页面的可见文本。
- 会话监控只有用户点击“开始监控”后才会采集。
- 只有用户点击“结束并上传”后才会上传本次会话。
- 只采集 `zhipin.com` 域名页面。
- 不自动登录 Boss 直聘。
- 不绕过平台权限。
- MVP 通过 URL query params 传输页面文本，`raw_text` 默认截取前 10000 字符。
