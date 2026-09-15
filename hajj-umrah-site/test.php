<?php
// test.php — فحص سريع للسيرفر
header('Content-Type: text/plain; charset=utf-8');
echo "PHP يعمل: " . phpversion() . "\n";
echo "MySQL PDO: " . (extension_loaded('pdo_mysql') ? 'نعم' : 'لا') . "\n";
echo "sqlite3: " . (extension_loaded('sqlite3') ? 'نعم' : 'لا') . "\n";
echo "وقت السيرفر: " . date('Y-m-d H:i:s') . "\n";