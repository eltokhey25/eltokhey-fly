<?php
/**
 * القالب الاحتياطي.
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
					<h1><?php the_title(); ?></h1>
					<div><?php the_content(); ?></div>
				</article>
			<?php endwhile; ?>
		<?php else : ?>
			<p class="text-center">لا توجد محتويات.</p>
		<?php endif; ?>
	</div>
</main>
<?php
get_footer();