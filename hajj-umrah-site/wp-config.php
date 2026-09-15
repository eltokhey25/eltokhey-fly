<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the installation.
 * You don't have to use the website, you can copy this file to "wp-config.php"
 * and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * Database settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://developer.wordpress.org/advanced-administration/wordpress/wp-config/
 *
 * @package WordPress
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'hajj_umrah_local' );

/** Database username */
define( 'DB_USER', 'root' );

/** Database password */
define( 'DB_PASSWORD', '' );

/** Database hostname */
define( 'DB_HOST', 'localhost' );

/** SQLite engine (يتم عبر إضافة SQLite Database Integration) */
define( 'DB_ENGINE', 'sqlite' );

/** يتم ضبط عنوان الموقع تلقائياً من إعدادات قاعدة البيانات (siteurl/home) */

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8mb4' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 *
 * Change these to different unique phrases! You can generate these using
 * the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}.
 *
 * You can change these at any point in time to invalidate all existing cookies.
 * This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define( 'AUTH_KEY',         'BuXUf92VZ8R3euQvkYKCyHuEpAUfp0_bybo2vJi8z2z-eKRkw2pKg9JKHEkYstmg' );
define( 'SECURE_AUTH_KEY',  '_WebF_iJeMzOfam8y4y2BmGHx9Gv1yhRrAPNq5c5C1wT3tYjMpQvuf72HS4OZcs3' );
define( 'LOGGED_IN_KEY',    'vzbElSUmQbV-sSjisMHKabQAwMkUspko4JXeCYl6agg9fjpYKBQ-bjhXaQ2fgGLC' );
define( 'NONCE_KEY',        'C6tsDXKYgQ3rSeErzdzb_PytItM8-I_gAhRJ41LCkfNsDoYvz-n7-3teD9hdcmyB' );
define( 'AUTH_SALT',        'baC3Hz-Fhq08zXA2WEnyn-bDcvvDauswJ5gKi-If-EZ8pQVn-dmtd_NZBdQYef4L' );
define( 'SECURE_AUTH_SALT', 'C-0z7lkg3dBvOD2yqiQagIJaQ3JPRMMXYphPOwy8orJE5R1l3lUYYLkqvillCAbM' );
define( 'LOGGED_IN_SALT',   'XFkWeQeRj8KEIVoigiodz_eymdFLGsT1XdFiOAoMfXLM99BE26mDTsuNeLPSxHtV' );
define( 'NONCE_SALT',       'uK6fMPM8XmAl1W7SpdqscLwMxG3z1eggo_Ky0W2QV4us7a7QEqk12ibme2bu5dHS' );

/**#@-*/

/**
 * WordPress database table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 *
 * At the installation time, database tables are created with the specified prefix.
 * Changing this value after WordPress is installed will make your site think
 * it has not been installed.
 *
 * @link https://developer.wordpress.org/advanced-administration/wordpress/wp-config/#table-prefix
 */
$table_prefix = 'wp_';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://developer.wordpress.org/advanced-administration/debug/debug-wordpress/
 */
define( 'WP_DEBUG', false );

/* === حماية أمان الموقع === */
/* تعطيل تعديل كود الملفات من لوحة التحكم (يجب استخدام FTP/SSH للتعديل) */
define( 'DISALLOW_FILE_EDIT', true );
/* إعادة تفعيل تحديث الإضافات والثيمات تلقائياً (الأهم أمنياً — الاستضافة المجانية موفرش SSH) */
/* لا نقوم بتعريف DISALLOW_FILE_MODS حتى تستطيع التحديثات التلقائية العمل */

/* === HTTPS إجباري === */
/* بعد التأكد أن شهادة SSL مجانية مفعلة (InfinityFree يقدمها تلقائياً):
   غيّر السطر التالي إلى true */
define( 'FORCE_SSL_ADMIN', false );

/* === رابط الموقع الديناميكي (local / الرابط العام عبر Tunnel) === */
$hu_scheme = 'http';
if ( isset( $_SERVER['HTTP_X_FORWARDED_PROTO'] ) && 'https' === $_SERVER['HTTP_X_FORWARDED_PROTO'] ) {
	$hu_scheme = 'https';
} elseif ( ! empty( $_SERVER['HTTPS'] ) && 'off' !== $_SERVER['HTTPS'] ) {
	$hu_scheme = 'https';
}
$hu_host = isset( $_SERVER['HTTP_HOST'] ) ? $_SERVER['HTTP_HOST'] : 'localhost:8080';
define( 'WP_HOME', $hu_scheme . '://' . $hu_host );
define( 'WP_SITEURL', $hu_scheme . '://' . $hu_host );
define( 'WP_CONTENT_URL', WP_SITEURL . '/wp-content' );

/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
