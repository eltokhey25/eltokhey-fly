<?php
/**
 * القالب العادي للصفحات.
 *
 * @package HajjUmrah
 */

get_header();
?>
<main class="page-gap">
	<div class="container">
		<?php if ( have_posts() ) : ?>
			<?php while ( have_posts() ) : the_post(); ?>
				<article>
					<h1 style="color:var(--primary);margin-bottom:20px;"><?php the_title(); ?></h1>
					<div class="trip-desc"><?php the_content(); ?></div>
				</article>
			<?php endwhile; ?>
		<?php endif; ?>
	</div>
</main>
<?php
get_footer();