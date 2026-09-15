<?php
/**
 * قالب: من نحن.
 * Template Name: من نحن
 *
 * @package HajjUmrah
 */

get_header();

$company = get_option( 'hu_company', 'رحلات الحج والعمرة' );
$phone   = get_option( 'hu_phone', '' );
$whats   = get_option( 'hu_whatsapp', '' );
?>
<section class="hero">
	<div class="container reveal">
		<h1>من نحن</h1>
		<p>تعرف على <?php echo esc_html( $company ); ?></p>
	</div>
</section>

<main class="page-gap">
	<div class="container">
		<div class="about-grid">
			<div class="trip-desc reveal-left">
				<h2 style="color:var(--primary);"><span style="color:var(--accent);">عن</span> شركتنا</h2>
				<?php the_content(); ?>
			</div>
			<div class="trip-desc reveal-right">
				<h2 style="color:var(--primary);">🗺 كيف ننظم برنامج السير؟</h2>
				<p>نضع لكل رحلة برنامج سير تفصيلي ومرتب، يبدأ من تجمّع ضمن المجموعة وتحديد نقطة الخروج، ثم الوصول إلى الأراضي المقدسة، ثم أداء المناسك يومياً مع فريق إرشادي، وحتى العودة بسلامة إلى نقطة الانطلاق.</p>
				<p>كل رحلة على الموقع تُعرض بترتيب أيامها كامل: مكان الخروج ← مدن الوصول ← أيام المشاعر ← العودة.</p>
			</div>
		</div>

		<div class="stats-grid">
			<div class="stat-card reveal"><strong>+15</strong><span>سنة خبرة</span></div>
			<div class="stat-card reveal"><strong>+2000</strong><span>حاج ومعتمر</span></div>
			<div class="stat-card reveal"><strong>4</strong><span>رحلات في السنة</span></div>
			<div class="stat-card reveal"><strong>100%</strong><span>ترخيص رسمي</span></div>
		</div>

		<?php if ( $phone || $whats ) : ?>
			<div class="text-center mt-2 reveal">
				<h2 class="cta-title" style="margin-bottom:14px;">تواصل معنا مباشرة</h2>
				<?php if ( $phone ) : ?><a class="btn" href="tel:<?php echo esc_attr( $phone ); ?>" style="margin-inline-end:10px;">📞 اتصل بنا</a><?php endif; ?>
				<?php if ( $whats ) : ?>
					<a class="btn btn-outline" href="https://wa.me/<?php echo esc_attr( $whats ); ?>" target="_blank" rel="noopener">💬 واتساب</a>
				<?php endif; ?>
			</div>
		<?php endif; ?>
	</div>
</main>
<?php
get_footer();