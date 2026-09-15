<?php
/**
 * كارت الرحلة — يُستخدم في الرئيسية وأرشيف الرحلات.
 *
 * @package HajjUmrah
 * @param int|WP_Post $trip
 */

if ( ! function_exists( 'trip_card' ) ) {
	function trip_card( $post_id ) {
		$price     = get_post_meta( $post_id, '_hu_price', true );
		$duration  = get_post_meta( $post_id, '_hu_duration', true );
		$departure = get_post_meta( $post_id, '_hu_departure', true );
		$transport = get_post_meta( $post_id, '_hu_transport', true );
		$remaining = get_post_meta( $post_id, '_hu_remaining', true );
		$active    = get_post_meta( $post_id, '_hu_active', true );
		$types     = wp_get_post_terms( $post_id, 'trip_type', array( 'fields' => 'names' ) );
		$slugs     = wp_get_post_terms( $post_id, 'trip_type', array( 'fields' => 'slugs' ) );

		if ( '1' !== $active ) {
			return;
		}

		$remaining = ( '' !== $remaining && null !== $remaining ) ? (int) $remaining : null;
		?>
		<article class="trip-card reveal" data-type="<?php echo esc_attr( implode( ',', $slugs ) ); ?>">
			<div class="trip-card-media">
				<?php if ( has_post_thumbnail() ) : ?>
					<?php the_post_thumbnail( 'large' ); ?>
				<?php else : ?>
					<div class="noimg">🕌</div>
				<?php endif; ?>
				<?php if ( ! empty( $types ) ) : ?>
					<span class="trip-type-badge"><?php echo esc_html( $types[0] ); ?></span>
				<?php endif; ?>
				<?php if ( $price ) : ?>
					<span class="trip-price-badge"><?php echo esc_html( number_format( (float) $price ) ); ?> ج.م</span>
				<?php endif; ?>
			</div>
			<div class="trip-card-body">
				<h3><a href="<?php echo esc_url( get_permalink( $post_id ) ); ?>"><?php echo esc_html( get_the_title( $post_id ) ); ?></a></h3>
				<div class="trip-meta">
					<?php if ( $departure ) : ?><span>📅 <?php echo esc_html( $departure ); ?></span><?php endif; ?>
					<?php if ( $duration ) : ?><span>⏱ <?php echo esc_html( $duration ); ?></span><?php endif; ?>
					<?php if ( $transport ) : ?><span>🚌 <?php echo esc_html( $transport ); ?></span><?php endif; ?>
				</div>
				<?php if ( null !== $remaining ) : ?>
					<span class="availability <?php echo ( $remaining > 0 ) ? 'ok' : 'full'; ?>">
						<?php echo ( $remaining > 0 ) ? '✓ الأماكن المتبقية: ' . (int) $remaining : '✕ مكتملة العدد'; ?>
					</span>
				<?php endif; ?>
				<a class="btn" href="<?php echo esc_url( get_permalink( $post_id ) ); ?>">عرض تفاصيل الرحلة</a>
			</div>
		</article>
		<?php
	}
}

trip_card( get_the_ID() );