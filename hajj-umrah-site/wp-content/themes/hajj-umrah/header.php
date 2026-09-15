<?php
/**
 * الترويسة.
 *
 * @package HajjUmrah
 */
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<?php
$company = get_option( 'hu_company', 'رحلات الحج والعمرة' );
$phone   = get_option( 'hu_phone', '' );
?>

<header class="site-header">
	<div class="header-top">
		<div class="container">
			<span>🌙 وكلاء رسميون للحج والعمرة — نخدمكم على مدار العام</span>
			<?php if ( $phone ) : ?>
				<a href="tel:<?php echo esc_attr( $phone ); ?>">📞 <?php echo esc_html( $phone ); ?></a>
			<?php endif; ?>
		</div>
	</div>
	<div class="container header-main">
		<a class="site-logo" href="<?php echo esc_url( home_url( '/' ) ); ?>">
			<span class="logo-mark">🕋</span>
			<span><?php echo esc_html( $company ); ?></span>
		</a>
		<nav class="main-nav" id="main-nav">
			<button class="nav-close" id="nav-close" aria-label="إغلاق القائمة">✕</button>
			<?php
			wp_nav_menu( array(
				'theme_location' => 'primary',
				'container'      => false,
				'fallback_cb'    => function () {
					echo '<ul>';
					echo '<li><a href="' . esc_url( home_url( '/' ) ) . '">' . esc_html__( 'الرئيسية', 'hajj-umrah' ) . '</a></li>';
					echo '<li><a href="' . esc_url( get_post_type_archive_link( 'trip' ) ) . '">' . esc_html__( 'رحلاتنا', 'hajj-umrah' ) . '</a></li>';
					echo '</ul>';
				},
			) );
			?>
			<a class="btn" href="<?php echo esc_url( home_url( '/booking/' ) ); ?>">احجز الآن</a>
		</nav>
		<button class="nav-toggle" id="nav-toggle" aria-label="القائمة">☰</button>
	</div>
</header>