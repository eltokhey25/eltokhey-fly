<?php
/**
 * صفحة تفاصيل الرحلة — برنامج السير مرتب من الخروج حتى العودة.
 *
 * @package HajjUmrah
 */

get_header();

while ( have_posts() ) :
	the_post();

	$price     = get_post_meta( get_the_ID(), '_hu_price', true );
	$duration  = get_post_meta( get_the_ID(), '_hu_duration', true );
	$departure = get_post_meta( get_the_ID(), '_hu_departure', true );
	$return    = get_post_meta( get_the_ID(), '_hu_return', true );
	$transport = get_post_meta( get_the_ID(), '_hu_transport', true );
	$capacity  = get_post_meta( get_the_ID(), '_hu_capacity', true );
	$remaining = get_post_meta( get_the_ID(), '_hu_remaining', true );
	$itinerary = get_post_meta( get_the_ID(), '_hu_itinerary', true );
	$includes  = get_post_meta( get_the_ID(), '_hu_includes', true );
	$excludes  = get_post_meta( get_the_ID(), '_hu_excludes', true );
	$types     = wp_get_post_terms( get_the_ID(), 'trip_type', array( 'fields' => 'names' ) );

	$whats = get_option( 'hu_whatsapp', '' );
	$phone = get_option( 'hu_phone', '' );
	$company = get_option( 'hu_company', '' );
	$title = get_the_title();

	$share_text = rawurlencode( "أرغب في الحجز في رحلة: {$title}" );
	$wa_link    = $whats ? "https://wa.me/{$whats}?text={$share_text}" : '';
	$capacity   = ( '' !== $capacity  && null !== $capacity )  ? (int) $capacity  : null;
	$remaining  = ( '' !== $remaining && null !== $remaining ) ? (int) $remaining : null;
	?>

	<section class="trip-hero">
		<div class="container reveal">
			<h1><?php the_title(); ?></h1>
			<?php if ( ! empty( $types ) ) : ?>
				<span class="trip-type-badge"><?php echo esc_html( $types[0] ); ?></span>
			<?php endif; ?>
			<div class="badges">
				<?php if ( $departure ) : ?><span>📅 الخروج: <?php echo esc_html( $departure ); ?></span><?php endif; ?>
				<?php if ( $return ) : ?><span>↩️ العودة: <?php echo esc_html( $return ); ?></span><?php endif; ?>
				<?php if ( $duration ) : ?><span>⏱ المدة: <?php echo esc_html( $duration ); ?></span><?php endif; ?>
				<?php if ( $transport ) : ?><span>🚌 <?php echo esc_html( $transport ); ?></span><?php endif; ?>
			</div>
		</div>
	</section>

	<div class="container trip-page">
		<div class="trip-content reveal-left">
			<?php if ( $itinerary_image = get_the_post_thumbnail_url( get_the_ID(), 'full' ) ) : ?>
				<img src="<?php echo esc_url( $itinerary_image ); ?>" alt="<?php echo esc_attr( get_the_title() ); ?>" style="border-radius:var(--radius);box-shadow:var(--shadow);">
			<?php endif; ?>

			<div class="trip-desc" style="margin-top:24px;">
				<h2>نبذة عن الرحلة</h2>
				<?php the_content(); ?>
			</div>

			<h2>برنامج السير بالتفصيل</h2>
			<p class="cta-sub" style="margin-bottom:20px;">يبدأ البرنامج من مكان الخروج وصولاً إلى العودة، بالترتيب الزمني الذي تسير به الرحلة.</p>

			<?php if ( ! empty( $itinerary ) && is_array( $itinerary ) ) : ?>
				<ol class="timeline">
					<?php foreach ( $itinerary as $i => $step ) : ?>
						<li class="timeline-item reveal">
							<span class="timeline-dot"><?php echo (int) $i + 1; ?></span>
							<div class="timeline-card">
								<?php if ( ! empty( $step['city'] ) ) : ?>
									<span class="step-city">📍 <?php echo esc_html( $step['city'] ); ?></span>
								<?php endif; ?>
								<h3><?php echo esc_html( $step['title'] ); ?></h3>
								<?php if ( ! empty( $step['desc'] ) ) : ?>
									<p><?php echo nl2br( esc_html( $step['desc'] ) ); ?></p>
								<?php endif; ?>
							</div>
						</li>
					<?php endforeach; ?>
				</ol>
			<?php else : ?>
				<p>لم تتم إضافة برنامج السير بعد لهذه الرحلة.</p>
			<?php endif; ?>

			<h2>المصاريف والاستثناءات</h2>
			<div class="trip-desc">
				<h3>يشمل السعر</h3>
				<ul class="list-checks">
					<?php if ( ! empty( $includes ) && is_array( $includes ) ) : ?>
						<?php foreach ( $includes as $inc ) : ?>
							<li><?php echo esc_html( $inc ); ?></li>
						<?php endforeach; ?>
					<?php else : ?>
						<li>لم تُضف بيانات بعد</li>
					<?php endif; ?>
				</ul>
				<h3 style="margin-top:20px;">لا يشمل السعر</h3>
				<ul class="list-checks no">
					<?php if ( ! empty( $excludes ) && is_array( $excludes ) ) : ?>
						<?php foreach ( $excludes as $exc ) : ?>
							<li><?php echo esc_html( $exc ); ?></li>
						<?php endforeach; ?>
					<?php else : ?>
						<li>لا توجد استثناءات</li>
					<?php endif; ?>
				</ul>
			</div>

			<div class="trip-desc" style="margin-top:24px;">
				<h2 style="margin:0;">معلومات التواصل مع <?php echo esc_html( $company ); ?></h2>
				<ul class="list-checks" style="margin-top:14px;">
					<?php if ( $phone ) : ?><li><a href="<?php echo esc_url( hu_tel_href( $phone ) ); ?>">📞 هاتف: <?php echo esc_html( $phone ); ?></a></li><?php endif; ?>
					<?php if ( $whats ) : ?><li><a href="<?php echo esc_url( hu_wa_href( $whats ) ); ?>" target="_blank" rel="noopener">💬 واتساب: <?php echo esc_html( $whats ); ?></a></li><?php endif; ?>
				</ul>
			</div>
		</div>

		<aside class="trip-aside reveal-right">
			<div class="summary-box">
				<h3>خلاصة الرحلة</h3>
				<ul class="summary-list">
					<?php if ( $types ) : ?><li><span>النوع</span><strong><?php echo esc_html( $types[0] ); ?></strong></li><?php endif; ?>
					<?php if ( $departure ) : ?><li><span>تاريخ الخروج</span><strong><?php echo esc_html( $departure ); ?></strong></li><?php endif; ?>
					<?php if ( $return ) : ?><li><span>تاريخ العودة</span><strong><?php echo esc_html( $return ); ?></strong></li><?php endif; ?>
					<?php if ( $duration ) : ?><li><span>المدة</span><strong><?php echo esc_html( $duration ); ?></strong></li><?php endif; ?>
					<?php if ( $transport ) : ?><li><span>النقل</span><strong><?php echo esc_html( $transport ); ?></strong></li><?php endif; ?>
					<?php if ( null !== $capacity ) : ?><li><span>السعة</span><strong><?php echo (int) $capacity; ?> شخص</strong></li><?php endif; ?>
				</ul>
				<div class="price-box">
					<?php if ( $price ) : ?>
						<span class="price"><?php echo esc_html( number_format( (float) $price ) ); ?> ج.م</span>
					<?php else : ?>
						<span class="price">اكتب لنا</span>
					<?php endif; ?>
					<?php if ( null !== $remaining ) : ?>
						<p style="margin-top:6px;" class="availability <?php echo ( $remaining > 0 ) ? 'ok' : 'full'; ?>">
							<?php echo ( $remaining > 0 ) ? '✓ الأماكن المتبقية: ' . (int) $remaining : '✕ مكتملة العدد — تواصل معنا للتسجيل في قائمة الانتظار'; ?>
						</p>
					<?php endif; ?>
				</div>
				<a class="btn" style="width:100%;text-align:center;margin-top:18px;" href="<?php echo esc_url( home_url( '/booking/' ) ); ?>">احجز هذه الرحلة</a>
				<?php if ( $wa_link ) : ?>
					<a class="btn btn-outline" style="width:100%;text-align:center;margin-top:10px;" href="<?php echo esc_url( $wa_link ); ?>" target="_blank" rel="noopener">💬 احجز عبر واتساب</a>
				<?php endif; ?>
			</div>
		</aside>
	</div>

	<?php
endwhile;

get_footer();