<?php
/**
 * قالب: تواصل / حجز.
 * Template Name: تواصل وحجز
 *
 * @package HajjUmrah
 */

get_header();

$phone   = get_option( 'hu_phone', '' );
$whats   = get_option( 'hu_whatsapp', '' );
$email   = get_option( 'hu_email', '' );
$address = get_option( 'hu_address', '' );
?>
<section class="hero">
	<div class="container reveal">
		<h1>تواصل وحجز</h1>
		<p>اختر رحلتك، احجز مكانك، وسنتواصل معك لتأكيد البيانات.</p>
	</div>
</section>

<main class="page-gap">
	<div class="container">
		<div class="contact-grid">
			<div class="reveal-left">
				<div class="info-card">
					<h3>بيانات التواصل</h3>
					<ul class="list-checks" style="margin-top:10px;">
						<?php if ( $phone ) : ?><li><a href="<?php echo esc_url( hu_tel_href( $phone ) ); ?>">📞 <?php echo esc_html( $phone ); ?></a></li><?php endif; ?>
						<?php if ( $whats ) : ?><li><a href="<?php echo esc_url( hu_wa_href( $whats ) ); ?>" target="_blank" rel="noopener">💬 واتساب: <?php echo esc_html( $whats ); ?></a></li><?php endif; ?>
						<?php if ( $email ) : ?><li><a href="mailto:<?php echo esc_attr( $email ); ?>">✉️ <?php echo esc_html( $email ); ?></a></li><?php endif; ?>
						<?php if ( $address ) : ?><li>📍 <?php echo esc_html( $address ); ?></li><?php endif; ?>
					</ul>
				</div>
				<div class="info-card">
					<h3>أوقات العمل</h3>
					<p>يومياً من 9 صباحاً حتى 10 مساءً</p>
				</div>
			</div>
			<div class="reveal-right">
				<h2 class="cta-title" style="margin-bottom:18px;">أرسل طلب الحجز</h2>
				<?php echo do_shortcode( '[hu_booking_form]' ); ?>
			</div>
		</div>
	</div>
</main>
<?php
get_footer();