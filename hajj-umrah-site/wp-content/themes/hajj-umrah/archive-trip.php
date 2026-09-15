<?php
/**
 * أرشيف الرحلات (جميع الرحلات).
 *
 * @package HajjUmrah
 */

get_header();
?>
<section class="hero">
	<div class="container reveal">
		<h1><?php the_archive_title(); ?></h1>
		<p>جميع رحلات الحج والعمرة مرتبة حسب موعد الانطلاق.</p>
	</div>
</section>

<section class="section">
	<div class="container">
		<div class="trip-filters reveal" id="trip-filters">
			<button class="filter-btn active" data-filter="all">كل الرحلات</button>
			<?php foreach ( hu_get_trip_types() as $ttype ) : ?>
				<button class="filter-btn" data-filter="<?php echo esc_attr( $ttype->slug ); ?>"><?php echo esc_html( $ttype->name ); ?></button>
			<?php endforeach; ?>
		</div>

		<?php if ( have_posts() ) : ?>
			<div class="trip-grid">
				<?php while ( have_posts() ) : the_post(); ?>
					<?php get_template_part( 'template-parts/trip-card' ); ?>
				<?php endwhile; ?>
			</div>
		<?php else : ?>
			<p class="text-center">لا توجد رحلات حالياً.</p>
		<?php endif; ?>
	</div>
</section>
<?php
get_footer();