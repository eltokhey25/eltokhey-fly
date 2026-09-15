<?php
/**
 * سكربت إعداد قاعدة البيانات SQLite
 * ════════════════════════════════════════
 * 
 * المطلوب:
 *   1. ارفع هذا الملف في مجلد htdocs/
 *   2. افتحه في المتصفح: http://eltokhey.site.je/setup-db.php
 *   3. اتبع التعليمات
 *   4. احذف الملف فوراً بعد الانتهاء!
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);

$messages = [];
$success = true;

// ─── 1. فحص PHP ───
$messages[] = "<h2>1. فحص PHP Extensions</h2>";

$pdo_sqlite = extension_loaded('pdo_sqlite');
$sqlite3    = extension_loaded('sqlite3');

if ($pdo_sqlite) {
    $messages[] = "<p style='color:green'>&#10003; pdo_sqlite: <b>مفعّل</b></p>";
} else {
    $messages[] = "<p style='color:red'>&#10007; pdo_sqlite: <b>غير مفعّل!</b> لازم تطلب من الاستضافة يفعّلوه</p>";
    $success = false;
}

if ($sqlite3) {
    $messages[] = "<p style='color:green'>&#10003; sqlite3: <b>مفعّل</b></p>";
} else {
    $messages[] = "<p style='color:orange'>&#9888; sqlite3: غير مفعّل (مشCritical — pdo_sqlite كافي)</p>";
}

$version = phpversion();
$messages[] = "<p>نسخة PHP: <b>$version</b></p>";

// ─── 2. فحص ملف wp-config.php ───
$messages[] = "<h2>2. فحص wp-config.php</h2>";

$wp_config = __DIR__ . '/wp-config.php';
if (file_exists($wp_config)) {
    $content = file_get_contents($wp_config);
    if (strpos($content, "define( 'DB_ENGINE', 'sqlite' )") !== false) {
        $messages[] = "<p style='color:green'>&#10003; wp-config.php فيه DB_ENGINE = sqlite</p>";
    } else {
        $messages[] = "<p style='color:orange'>&#9888; wp-config.php ما فيه DB_ENGINE — تأكد إنه موجود</p>";
    }
} else {
    $messages[] = "<p style='color:red'>&#10007; wp-config.php مش موجود! ارفع الملفات أولاً</p>";
    $success = false;
}

// ─── 3. فحص مجلد database ───
$messages[] = "<h2>3. فحص مجلد wp-content/database/</h2>";

$db_dir = __DIR__ . '/wp-content/database';
if (!is_dir($db_dir)) {
    $messages[] = "<p style='color:orange'>&#9888; مجلد wp-content/database/ مش موجود — جاري إنشاؤه...</p>";
    @mkdir($db_dir, 0700, true);
    if (is_dir($db_dir)) {
        $messages[] = "<p style='color:green'>&#10003; تم إنشاء المجلد بنجاح</p>";
    } else {
        $messages[] = "<p style='color:red'>&#10007; ما قدرنا نعمل المجلد — اعمله يدوياً وحط صلاحيات 700</p>";
        $success = false;
    }
} else {
    $perms = substr(sprintf('%o', fileperms($db_dir)), -4);
    $messages[] = "<p style='color:green'>&#10003; المجلد موجود (صلاحيات: $perms)</p>";
}

// ─── 4. فحص / نقل ملف قاعدة البيانات ───
$messages[] = "<h2>4. فحص ملف قاعدة البيانات</h2>";

$ht_sqlite   = $db_dir . '/.ht.sqlite';
$db_sqlite   = $db_dir . '/database.sqlite';
$wp_db_php   = $db_dir . '/wp-db.php';
$index_php   = $db_dir . '/index.php';

// عمل index.php لو مش موجود (حماية)
if (!file_exists($index_php)) {
    file_put_contents($index_php, "<?php\n// Silence is golden.\n");
    $messages[] = "<p style='color:green'>&#10003; تم إنشاء index.php للحماية</p>";
}

// فحص database/.htaccess
$htaccess = $db_dir . '/.htaccess';
if (!file_exists($htaccess)) {
    file_put_contents($htaccess, "Require all denied\nOrder Deny,Allow\nDeny from all\n");
    $messages[] = "<p style='color:green'>&#10003; تم إنشاء .htaccess للحماية</p>";
} else {
    $perms = substr(sprintf('%o', fileperms($htaccess)), -4);
    $messages[] = "<p style='color:green'>&#10003; .htaccess موجود (صلاحيات: $perms)</p>";
}

if (file_exists($ht_sqlite)) {
    $size = filesize($ht_sqlite);
    $size_mb = round($size / 1024 / 1024, 2);
    @chmod($ht_sqlite, 0600);
    $messages[] = "<p style='color:green'>&#10003; .ht.sqlite موجود ($size_mb MB) — الصلاحيات: 600</p>";
} elseif (file_exists($db_sqlite)) {
    $size = filesize($db_sqlite);
    $size_mb = round($size / 1024 / 1024, 2);
    $messages[] = "<p style='color:orange'>&#9888; لقيت database.sqlite بدل .ht.sqlite — جاري النقل...</p>";
    $renamed = @rename($db_sqlite, $ht_sqlite);
    if ($renamed) {
        @chmod($ht_sqlite, 0600);
        $messages[] = "<p style='color:green'>&#10003; تم النقل بنجاح ($size_mb MB) — الصلاحيات: 600</p>";
    } else {
        $messages[] = "<p style='color:red'>&#10007; ما قدرنا ننقل الملف — اعملها يدوياً:<br>";
        $messages[] = "<code>mv wp-content/database/database.sqlite wp-content/database/.ht.sqlite</code></p>";
        $success = false;
    }
} else {
    $messages[] = "<p style='color:red'>&#10007; لا يوجد ملف قاعدة بيانات! ارفع database.sqlite في wp-content/database/ وأعد تشغيل هذا الملف</p>";
    $success = false;
}

// ─── 5. فحص WPB path ───
$messages[] = "<h2>5. فحص ملف wp-db.php</h2>";

$wpdb_php = __DIR__ . '/wp-content/db.php';
if (file_exists($wpdb_php)) {
    $content = file_get_contents($wpdb_php);
    if (strpos($content, 'SQLITE') !== false || strpos($content, 'sqlite') !== false || strpos($content, '.ht.sqlite') !== false) {
        $messages[] = "<p style='color:green'>&#10003; wp-content/db.php موجود ومتصل بـ SQLite</p>";
    } else {
        $messages[] = "<p style='color:orange'>&#9888; wp-content/db.php موجود لكن تأكد إنه مرتبط بـ SQLite</p>";
    }
} else {
    $messages[] = "<p style='color:red'>&#10007; wp-content/db.php مش موجود! لازم يكون موجود لـ SQLite integration</p>";
    $success = false;
}

// ─── 6. فحص SVN/WordPress ───
$messages[] = "<h2>6. فحص WordPress</h2>";

$wp_inc = __DIR__ . '/wp-includes';
if (is_dir($wp_inc)) {
    $messages[] = "<p style='color:green'>&#10003; مجلد wp-includes موجود</p>";
} else {
    $messages[] = "<p style='color:red'>&#10007; مجلد wp-includes مش موجود — ارفع الملفات أولاً!</p>";
    $success = false;
}

// ─── النتيجة ───
echo "<!DOCTYPE html><html dir='rtl'><head><meta charset='utf-8'>";
echo "<title>إعداد قاعدة البيانات SQLite</title>";
echo "<style>";
echo "body { font-family: Tahoma, Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; background: #f5f5f5; }";
echo "h1 { background: #2c3e50; color: white; padding: 15px; border-radius: 5px; }";
echo "h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }";
echo ".success { background: #d4edda; border: 1px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0; }";
echo ".error { background: #f8d7da; border: 1px solid #dc3545; padding: 15px; border-radius: 5px; margin: 20px 0; }";
echo ".info { background: #d1ecf1; border: 1px solid #17a2b8; padding: 15px; border-radius: 5px; margin: 20px 0; }";
echo "code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; }";
echo "button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }";
echo "button:hover { background: #2980b9; }";
echo "</style></head><body>";

echo "<h1>&#9881; إعداد قاعدة البيانات SQLite</h1>";

echo "<div class='info'>";
echo "<p><strong>&#9888; تعليمات مهمة:</strong></p>";
echo "<ol>";
echo "<li>ارفع هذا الملف في مجلد <code>htdocs/</code></li>";
echo "<li>ارفع <code>database.sqlite</code> في <code>htdocs/wp-content/database/</code></li>";
echo "<li>افتح هذا الرابط في المتصفح</li>";
echo "<li>بعد ما تتأكد كل شي أخضر، احذف هذا الملف فوراً!</li>";
echo "</ol>";
echo "</div>";

foreach ($messages as $msg) {
    echo $msg;
}

if ($success) {
    echo "<div class='success'>";
    echo "<h2>&#10003; كل شي جاهز!</h2>";
    echo "<p>ممكن تفتح الموقع: <a href='http://eltokhey.site.je/' target='_blank'>http://eltokhey.site.je/</a></p>";
    echo "<p>لو دخلت على لوحة التحكم: <a href='http://eltokhey.site.je/wp-admin/' target='_blank'>http://eltokhey.site.je/wp-admin/</a></p>";
    echo "<br><p style='color:red'><strong>&#10007; احذف هذا الملف فوراً!</strong></p>";
    echo "<form method='post' style='margin-top:10px'>";
    echo "<input type='hidden' name='delete_self' value='1'>";
    echo "<button type='submit' style='background:red'>&#10007; احذف setup-db.php الآن</button>";
    echo "</form>";
    echo "</div>";
} else {
    echo "<div class='error'>";
    echo "<h2>&#10007; في مشاكل لازم تتحل</h2>";
    echo "<p>اقرأ الأخطاء فوق وحلها، ثم أعد تشغيل هذا الملف</p>";
    echo "</div>";
}

// ─── حذف نفس الملف ───
if (isset($_POST['delete_self']) && $_POST['delete_self'] == '1') {
    $self = __FILE__;
    if (file_exists($self)) {
        @unlink($self);
        echo "<div class='success'>";
        echo "<h2>&#10003; تم حذف setup-db.php بنجاح</h2>";
        echo "</div>";
    }
}

echo "</body></html>";
