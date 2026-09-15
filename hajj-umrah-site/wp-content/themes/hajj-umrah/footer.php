<?php
/**
 * التذييل.
 *
 * @package HajjUmrah
 */
$company = get_option( 'hu_company', 'رحلات الحج والعمرة' );
$phone   = get_option( 'hu_phone', '' );
$whats   = get_option( 'hu_whatsapp', '' );
$email   = get_option( 'hu_email', '' );
$address = get_option( 'hu_address', '' );
$fb      = get_option( 'hu_fb', '' );
?>

<footer class="site-footer">
	<div class="container footer-grid reveal">
		<div>
			<h3><?php echo esc_html( $company ); ?></h3>
			<p>نساعدك على أداء مناسك الحج والعمرة بأفضل صورة، مع برنامج سير منظَّم ومرافقين معتمدين، منذ لحظة الخروج من مقر إقامتك حتى عودتك إليها.</p>
		</div>
		<div>
			<h3>روابط سريعة</h3>
			<ul>
				<li><a href="<?php echo esc_url( home_url( '/' ) ); ?>">الرئيسية</a></li>
				<li><a href="<?php echo esc_url( get_post_type_archive_link( 'trip' ) ); ?>">رحلاتنا</a></li>
				<li><a href="<?php echo esc_url( home_url( '/booking/' ) ); ?>">تواصل / حجز</a></li>
				<li><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>">من نحن</a></li>
			</ul>
		</div>
		<div>
			<h3>بيانات التواصل</h3>
			<ul>
				<?php if ( $phone ) : ?><li><a href="<?php echo esc_url( hu_tel_href( $phone ) ); ?>">📞 <?php echo esc_html( $phone ); ?></a></li><?php endif; ?>
				<?php if ( $whats ) : ?><li><a href="<?php echo esc_url( hu_wa_href( $whats ) ); ?>" target="_blank" rel="noopener">💬 واتساب: <?php echo esc_html( $whats ); ?></a></li><?php endif; ?>
				<?php if ( $email ) : ?><li><a href="mailto:<?php echo esc_attr( $email ); ?>">✉️ <?php echo esc_html( $email ); ?></a></li><?php endif; ?>
				<?php if ( $address ) : ?><li>📍 <?php echo esc_html( $address ); ?></li><?php endif; ?>
				<?php if ( $fb ) : ?><li><a href="<?php echo esc_url( $fb ); ?>" target="_blank" rel="noopener">فيسبوك</a></li><?php endif; ?>
			</ul>
		</div>
	</div>
	<div class="footer-bottom">
		<div class="container">
			<span class="footer-copy">© <?php echo esc_html( date( 'Y' ) ); ?> <?php echo esc_html( $company ); ?> — جميع الحقوق محفوظة.</span>
			<?php $fb = get_option( 'hu_fb', '' ); ?>
			<?php if ( $fb ) : ?>
				<span class="footer-credit">
					<span class="credit-label">Developed by</span>
					<a href="<?php echo esc_url( $fb ); ?>" target="_blank" rel="noopener" aria-label="Engineer Mohamed El-Tokhey on Facebook">
						<strong>مهندس محمد الطوخي</strong>
					</a>
				</span>
			<?php endif; ?>
		</div>
	</div>
</footer>

<?php if ( $phone ) : ?>
	<a class="fab fab-call" href="<?php echo esc_url( hu_tel_href( $phone ) ); ?>" aria-label="اتصال سريع">📞</a>
<?php endif; ?>
<?php if ( $whats ) : ?>
	<a class="fab fab-wa" href="<?php echo esc_url( hu_wa_href( $whats ) ); ?>" target="_blank" rel="noopener" aria-label="تواصل عبر واتساب">💬</a>
<?php endif; ?>

<?php wp_footer(); ?>
</body>
</html>