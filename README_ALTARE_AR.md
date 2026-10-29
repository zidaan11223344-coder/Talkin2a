# تشغيل Talkin2a على Altare

## المتغيرات المطلوبة

ضع المتغيرات السرية من لوحة Altare في **Environment Variables**، ولا تضع كلمات المرور داخل Git أو Dockerfile:

```text
BOT_ID=اسم_البوت
BOT_PWD=كلمة_مرور_البوت
BOT_MASTER=اسم_الماستر
GROUP_TO_JOIN=اسم_الغرفة_الأولى
```

## قاعدة Talkin ID Data

إذا أعطتك خدمة قاعدة البيانات رابطًا واحدًا، استخدم:

```text
TALKIN_ID_DATA_DATABASE_URL=رابط_قاعدة_البيانات
```

ويقبل المشروع أيضًا اسم المنصة القياسي:

```text
DATABASE_URL=رابط_قاعدة_البيانات
```

إذا كانت المنصة تعطي حقولًا منفصلة، استخدم الأسماء التالية:

```text
TALKIN_ID_DATA_DATABASE_KIND=mysql
TALKIN_ID_DATA_DB_HOST=عنوان_الخادم
TALKIN_ID_DATA_DB_PORT=3306
TALKIN_ID_DATA_DB_NAME=talkin_bot_db
TALKIN_ID_DATA_DB_USER=اسم_المستخدم
TALKIN_ID_DATA_DB_PASSWORD=كلمة_المرور
```

يدعم الكود كذلك `DB_*` و`MYSQL_*` و`POSTGRES_*` و`RIVEN_*`. عند التشغيل ينشئ جدول `bot_state` تلقائيًا، ويكتب في سجل Altare إحدى الرسائل التالية:

- `[STATE-DB] MYSQL enabled: ...` أو `[STATE-DB] POSTGRES enabled: ...` عند نجاح الاتصال.
- `[STATE-DB] disabled after connection failure: ...` عند فشل الاتصال.
- `[STATE-DB] disabled: no usable Talkin ID Data/DATABASE_URL credentials found` عند غياب بيانات الاتصال.

## حفظ الملفات والمتغيرات

ملفات الحالة JSON تُرفع إلى مستودع بيانات Talkin-ID-Data:

```text
GITHUB_REPO=zidaan11223344-coder/Talkin-ID-Data
GITHUB_DATA_DIR=bot_data
GITHUB_SYNC=1
GITHUB_TOKEN=<توكن_لديه_صلاحية_الكتابة_إلى_Talkin-ID-Data>
```

لا تضع `GITHUB_TOKEN` داخل الملفات المرفوعة إلى المستودع. إذا كانت قيمة
`GITHUB_REPO` موجودة في Altare، اجعلها `zidaan11223344-coder/Talkin-ID-Data` حتى لا
يعود النسخ الاحتياطي إلى مستودع آخر.

أنشئ Persistent Volume في Altare واربطه داخل الحاوية بالمسار `/data`، ثم ضع:

```text
BOT_DATA_DIR=/data/talkin2
PERSISTENT_DATA_DIR=/data/talkin2
TELEGRAM_LOG_FILE=/data/talkin2/bot_runtime.log
TELEGRAM_CHAT_FILE=/data/talkin2/telegram_chat_id.json
```

متغيرات البيئة نفسها يجب حفظها من لوحة Altare. مجلد Volume يحفظ ملفات الحالة والسجل فقط؛ لا يعتمد المشروع على كتابة الأسرار إلى ملفات داخل المستودع.

## منع دخول جميع الغرف عند التشغيل أو إعادة الاتصال

لمنع استعادة الغرف المحفوظة تلقائيًا، ضع:

```text
RESTORE_SAVED_ROOMS_ON_STARTUP=0
```

في هذه الحالة يدخل البوت تلقائيًا إلى `GROUP_TO_JOIN` فقط. ويمكن استخدام أوامر دخول الغرف يدويًا بعد التشغيل. ولإعادة السلوك القديم:

```text
RESTORE_SAVED_ROOMS_ON_STARTUP=1
```

ولمنع **أي دخول تلقائي**، بما في ذلك `GROUP_TO_JOIN`، ضع:

```text
STARTUP_JOIN_ENABLED=0
```

وعندها لا يحتاج التشغيل إلى `GROUP_TO_JOIN`، وتبقى أوامر الدخول اليدوية متاحة.

## سجل الاتصال

سيظهر في Runtime Logs ما إذا تم الاتصال، مثل:

```text
[AUTH] result= ...
[WS] CONNECTED: wss://...
```

وتظهر أخطاء المصادقة أو WebSocket أو قاعدة البيانات حتى لو كانت `QUIET_MODE=1`، دون طباعة كلمات المرور أو مفاتيح الاتصال.
