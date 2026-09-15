<?php
// Router للسيرفر المدمج — يدعم الروابط الجميلة (pretty permalinks)

// لو الطلب جاي عبر نفق Cloudflare (HTTPS) نعامل الاتصال كـ HTTPS
$hu_proto = $_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '';
if ( 'https' === $hu_proto || ( isset( $_SERVER['HTTP_CF_VISITOR'] ) && false !== strpos( $_SERVER['HTTP_CF_VISITOR'], '"https"' ) ) ) {
	$_SERVER['HTTPS']      = 'on';
	$_SERVER['SERVER_PORT'] = '443';
}

$uri = urldecode( parse_url( $_SERVER['REQUEST_URI'], PHP_URL_PATH ) );

if ( preg_match( '#^/(xmlrpc\.php|wp-comments-post\.php|wp-trackback\.php)$#i', $uri ) ) {
	http_response_code( 403 );
	exit;
}

if ( '/' !== $uri && file_exists( __DIR__ . $uri ) ) {
	$parts = explode( '/', trim( $uri, '/' ) );
	foreach ( $parts as $part ) {
		if ( str_starts_with( $part, '.' ) ) {
			http_response_code( 403 );
			exit;
		}
	}
	return false;
}

require __DIR__ . '/index.php';