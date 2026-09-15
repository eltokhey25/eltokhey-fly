<?php
/**
 * صفحة 404 — الرابط غير موجود.
 *
 * @package HajjUmrah
 */

get_header();
?>
<section class="hero">
	<div class="container">
		<h1>404 — الصفحة غير موجودة</h1>
		<p>عذراً، الرابط الذي تحاول الوصول إليه غير موجود أو تم نقله.</p>
	</div>
</section>

<section class="section">
	<div class="container text-center">
		<h2 style="color:var(--primary);margin-bottom:14px;">يمكنك العودة لاستكشاف رحلاتنا</h2>
		<a class="btn" href="<?php echo esc_url( home_url( '/' ) ); ?>" style="margin-inline-end:10px;">🏠 العودة للرئيسية</a>
		<a class="btn btn-outline" href="<?php echo esc_url( home_url( '/trips/' ) ); ?>">🕋 تصفح الرحلات</a>
	</div>
</section>
<?php
get_footer();