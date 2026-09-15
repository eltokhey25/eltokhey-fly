<?php
/**
 * Plugin Name: سكوريتي هاردننغ — Hajj & Umrah
 * Description: حماية شاملة: رؤوس أمان، منع حصر المستخدمين، تقييد تسجيل الدخول، تعطيل pingbacks.
 * Version: 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* 1) رؤوس الأمان — تعمل على أي سيرفر (مش بس .htaccess) */
add_action( 'send_headers', function () {
	if ( headers_sent() ) {
		return;
	}
	header( 'X-Content-Type-Options: nosniff' );
	header( 'X-Frame-Options: SAMEORIGIN' );
	header( 'X-XSS-Protection: 1; mode=block' );
	header( 'Referrer-Policy: strict-origin-when-cross-origin' );
	header( 'Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()' );
} );

/* 2) منع حصر أسماء المستخدمين عبر /?author=N */
add_action( 'template_redirect', function () {
	if ( isset( $_GET['author'] ) || preg_match( '#/author/.*#i', $_SERVER['REQUEST_URI'] ?? '' ) ) {
		wp_redirect( home_url( '/' ), 301 );
		exit;
	}
} );

/* 3) منع كشف المستخدمين عبر REST API */
add_filter( 'rest_endpoints', function ( $endpoints ) {
	if ( isset( $endpoints['/wp/v2/users'] ) ) {
		unset( $endpoints['/wp/v2/users'] );
	}
	if ( isset( $endpoints['/wp/v2/users/(?P<id>[\d]+)'] ) ) {
		unset( $endpoints['/wp/v2/users/(?P<id>[\d]+)'] );
	}
	unset( $endpoints['/wp/v2/users/me'] );
	return $endpoints;
} );

/* 4) تعطيل pingbacks و trackbacks (يمنع استغلال SSRF) */
add_filter( 'xmlrpc_enabled', '__return_false' );
add_filter( 'pre_ping', '__return_empty_array' );
add_filter( 'pings_open', '__return_false' );

/* 5) إزالة وسم إصدار ووردبريس من رأس الصفحة */
add_filter( 'the_generator', '__return_empty_string' );

/* 6) تقييد محاولات تسجيل الدخول الفاشلة (5 محاولات / 15 دقيقة) */
add_filter( 'authenticate', function ( $user, $username, $password ) {
	if ( empty( $username ) ) {
		return $user;
	}
	$key      = 'hu_login_attempts_' . md5( strtolower( $username ) );
	$attempts = (int) get_transient( $key );
	$limit    = 5;
	$lockout  = 15 * MINUTE_IN_SECONDS;

	if ( $attempts >= $limit ) {
		$wait = $lockout - ( time() - (int) get_transient( $key . '_time' ) );
		if ( $wait > 0 ) {
			return new WP_Error(
				'too_many_attempts',
				sprintf( 'تم تجاوز عدد محاولات الدخول. أعد المحاولة بعد %d دقيقة.', ceil( $wait / 60 ) )
			);
		}
		set_transient( $key, 0, $lockout );
	}

	if ( is_wp_error( $user ) ) {
		$count = (int) get_transient( $key ) + 1;
		set_transient( $key, $count, $lockout );
		set_transient( $key . '_time', time(), $lockout );
	}

	return $user;
}, 20, 3 );

/* 8) عدم إظهار أخطاء PHP للزوار */
if ( ! defined( 'WP_DEBUG_DISPLAY' ) || WP_DEBUG_DISPLAY ) {
	@ini_set( 'display_errors', '0' );
}

/* 7) تحديد مدة الاحتفاظ بسجلات AI إلى 30 يوم */
add_filter( 'wpai_request_log_retention_days', function () {
	return 30;
} );

/* 9) منع سرد محتوى المرفقات والصفحات الحساسة في محركات البحث */
add_filter( 'wp_robots', function ( $robots ) {
	if ( is_user_logged_in() ) {
		return $robots;
	}
	if ( is_attachment() || is_search() || is_404() ) {
		$robots['noindex'] = true;
	}
	return $robots;
} );
