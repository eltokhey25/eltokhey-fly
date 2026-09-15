<?php
/**
 * الصفحة الرئيسية — عرض كل رحلات السنة مع فلترة الحج والعمرة.
 *
 * النصوص وترتيب الأقسام قابلة للتعديل من لوحة التحكم (صفحة "معاينة الموقع").
 *
 * @package HajjUmrah
 */

get_header();

$hero_title  = get_option( 'hu_hero_title', 'رحلات الحج والعمرة لكل مواسم السنة' );
$hero_sub    = get_option( 'hu_hero_sub', 'تعرّف على رحلاتنا بتفاصيل كاملة لأيام السير، من نقطة الخروج حتى العودة، واحجز مكانك في المواعيد المتاحة.' );
$explore_btn = get_option( 'hu_hero_btn', 'استكشف رحلات السنة' );
$trips_title = get_option( 'hu_trips_title', 'رحلات السنة' );
$trips_sub   = get_option( 'hu_trips_sub', 'جميع رحلات الحج والعمرة مرتبة حسب موعد الانطلاق، اضغط على أي رحلة لعرض برنامج السير بالتفصيل من الخروج حتى العودة.' );
$why_title   = get_option( 'hu_why_title', 'لماذا تختارنا؟' );
$cta_title   = get_option( 'hu_cta_title', 'جاهز تبدأ رحلتك المباركة؟' );
$cta_sub     = get_option( 'hu_cta_sub', 'تواصل معنا الآن واحجز مكانك في أقرب رحلة.' );
$phone       = get_option( 'hu_phone', '' );

$q = hu_get_upcoming_trips();

foreach ( hu_home_sections() as $slug ) :
	switch ( $slug ) {
		case 'hero':
			?>
			<section class="hero">
				<div class="container reveal">
					<h1><?php echo esc_html( $hero_title ); ?></h1>
					<p><?php echo esc_html( $hero_sub ); ?></p>
					<a class="btn btn-light" href="#trips"><?php echo esc_html( $explore_btn ); ?></a>
				</div>
			</section>
			<?php
			break;

		case 'trips':
			?>
			<section class="section" id="trips">
				<div class="container">
					<div class="section-head reveal">
						<h2><?php echo esc_html( $trips_title ); ?></h2>
						<p><?php echo esc_html( $trips_sub ); ?></p>
					</div>

					<div class="trip-filters reveal" id="trip-filters">
						<button class="filter-btn active" data-filter="all">كل الرحلات</button>
						<?php foreach ( hu_get_trip_types() as $ttype ) : ?>
							<button class="filter-btn" data-filter="<?php echo esc_attr( $ttype->slug ); ?>"><?php echo esc_html( $ttype->name ); ?></button>
						<?php endforeach; ?>
					</div>

					<?php if ( $q->have_posts() ) : ?>
						<div class="trip-grid">
							<?php while ( $q->have_posts() ) : $q->the_post(); ?>
								<?php get_template_part( 'template-parts/trip-card' ); ?>
							<?php endwhile; ?>
						</div>
						<?php wp_reset_postdata(); ?>
					<?php else : ?>
						<p class="text-center">لم تتم إضافة رحلات بعد. سيقوم المشرف بإضافة الرحلات من لوحة التحكم.</p>
					<?php endif; ?>
				</div>
			</section>
			<?php
			break;

		case 'why':
			?>
			<section class="section">
				<div class="container">
					<div class="section-head reveal">
						<h2><?php echo esc_html( $why_title ); ?></h2>
					</div>
					<div class="trip-grid">
						<div class="trip-card reveal">
							<div class="trip-card-body">
								<h3>🕋 رحلات مُرخصة ورسمية</h3>
								<p>نعمل بتراخيص رسمية من الجهات المعنية لتنظيم موسمي الحج والعمرة.</p>
							</div>
						</div>
						<div class="trip-card reveal">
							<div class="trip-card-body">
								<h3>🗺 برنامج سير مُنظَّم</h3>
								<p>كل رحلة لها برنامج سير يومي واضح منذ الخروج وحتى العودة إلى مكان إقامتك.</p>
							</div>
						</div>
						<div class="trip-card reveal">
							<div class="trip-card-body">
								<h3>🙋 مرافقون معتمدون</h3>
								<p>مشايخ ومرشدون متخصصون يرافقون المجموعة لإروائهم بأحكام المناسك.</p>
							</div>
						</div>
						<div class="trip-card reveal">
							<div class="trip-card-body">
								<h3>🛏 سكن وإقامة مريحة</h3>
								<p>إقامة قريبة من الحرمين الشريفين ووسائل نقل مريحة طوال الرحلة.</p>
							</div>
						</div>
					</div>
				</div>
			</section>
			<?php
			break;

		case 'cta':
			?>
			<section class="section">
				<div class="container text-center reveal">
					<h2 class="cta-title" style="margin-bottom:10px;"><?php echo esc_html( $cta_title ); ?></h2>
					<p class="cta-sub" style="margin-bottom:20px;"><?php echo esc_html( $cta_sub ); ?></p>
					<?php if ( $phone ) : ?>
						<a class="btn" href="tel:<?php echo esc_attr( $phone ); ?>" style="margin-inline-end:10px;">📞 اتصل الآن</a>
					<?php endif; ?>
					<a class="btn btn-outline" href="<?php echo esc_url( home_url( '/booking/' ) ); ?>">احجز رحلتك</a>
				</div>
			</section>
			<?php
			break;
	}
endforeach;

get_footer();