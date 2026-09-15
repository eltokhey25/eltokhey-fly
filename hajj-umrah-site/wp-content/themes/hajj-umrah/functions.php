<?php
/**
 * Hajj & Umrah theme functions.
 *
 * @package HajjUmrah
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'HU_VERSION', '1.2.0' );

define( 'HU_FIXED_ITINERARY', array(
	array(
		'title' => 'التجمع وتحديد نقطة الخروج',
		'city'  => 'القاهرة',
		'desc'  => 'التجمع في مقر البداية واستلام جوازات السفر والتحقق من الأوراق، ثم الانطلاق بالطيران من مطار القاهرة.',
	),
	array(
		'title' => 'الوصول إلى مطار جدة',
		'city'  => 'جدة',
		'desc'  => 'استقبال المجموعة في مطار جدة الدولي والانتقال بالفندق في جدة لليلة الراحة الأولى.',
	),
	array(
		'title' => 'الوصول إلى مكة المكرمة',
		'city'  => 'مكة المكرمة',
		'desc'  => 'الانتقال إلى الفندق القريب من الحرم، أداء العمرة الأولى وطواف القدوم.',
	),
	array(
		'title' => 'أداء المناسك والعبادة',
		'city'  => 'مكة المكرمة',
		'desc'  => 'زيارة مسجد قباء والمدينة المنورة برفق المشايخ، وأداء العمرات المتعددة.',
	),
	array(
		'title' => 'السفر إلى المدينة المنورة',
		'city'  => 'المدينة المنورة',
		'desc'  => 'زيارة المسجد النبوي الشريف وأداء الصلوات فيه، والذهاب إلى قبور الصحابة.',
	),
	array(
		'title' => 'العودة إلى مصر',
		'city'  => 'القاهرة',
		'desc'  => 'السفر من مطار المدينة إلى مطار القاهرة والعودة إلى نقطة الخروج نفسها.',
	),
) );

define( 'HU_FIXED_DURATION', '15 يوم' );
define( 'HU_FIXED_RETURN_DAYS', 14 );
define( 'HU_RAMADAN_DURATION', '40 يوم' );
define( 'HU_RAMADAN_RETURN_DAYS', 39 );
define( 'HU_FIXED_TRANSPORT', 'طيران' );
define( 'HU_FIXED_CAPACITY', 45 );

define( 'HU_FIXED_ITINERARY_RAMADAN', array(
	array(
		'title' => 'التجمع وتحديد نقطة الخروج',
		'city'  => 'القاهرة',
		'desc'  => 'التجمع في مقر البداية واستلام جوازات السفر والتحقق من الأوراق، ثم الانطلاق بالطيران من مطار القاهرة.',
	),
	array(
		'title' => 'الطيران إلى مطار جدة',
		'city'  => 'جدة',
		'desc'  => 'استقبال المجموعة في مطار جدة الدولي والانتقال بالفندق في جدة لليلة الراحة الأولى.',
	),
	array(
		'title' => 'التوجه إلى مكة المكرمة',
		'city'  => 'مكة المكرمة',
		'desc'  => 'النزول في الفندق القريب من الحرم المكي، وأداء العمرة الأولى وطواف القدوم في أول أيام رمضان.',
	),
	array(
		'title' => 'ليالي رمضان الأولى في الحرم المكي',
		'city'  => 'مكة المكرمة',
		'desc'  => 'أداء الصلوات والقيام والتلاوة في الحرم المكي مع زيارات متعددة لفروع المسجد الحرام، والاعتداد بأجواء أول عشر ليالٍ من رمضان.',
	),
	array(
		'title' => 'الإفطار الجماعي اليومي',
		'city'  => 'مكة المكرمة',
		'desc'  => 'موائد إفطار جماعية منظمة للفرقة في الفندق القريب من الحرم، مع برنامج روحاني بعد الفطور حتى صلاة التراويح.',
	),
	array(
		'title' => 'عمرات متعددة في الأسبوع الأول',
		'city'  => 'مكة المكرمة',
		'desc'  => 'أداء العمرات المتعددة بين الأذانين مع المرشدين الشرعيين، وزيارة توسعات الحرم والمنطقة المحيطة.',
	),
	array(
		'title' => 'زيارة غار حراء وجبل النور',
		'city'  => 'مكة المكرمة',
		'desc'  => 'التوجه برفقة المشايخ إلى جبل النور وزيارة غار حراء، مع الشرح الشرعي لسيرة النبي ﷺ.',
	),
	array(
		'title' => 'السفر إلى المدينة المنورة',
		'city'  => 'المدينة المنورة',
		'desc'  => 'السفر بالحافلة إلى المدينة المنورة، والنزول في الفندق القريب من المسجد النبوي وزيارة الروضة الشريفة.',
	),
	array(
		'title' => 'زيارة معالم المدينة',
		'city'  => 'المدينة المنورة',
		'desc'  => 'زيارة مسجد قباء ومسجد القبلتين ومقبرة البقيع وجبل أحد، مع المرشدين الشرعيين أيام المدينة كاملة.',
	),
	array(
		'title' => 'أيام العبادة في المسجد النبوي',
		'city'  => 'المدينة المنورة',
		'desc'  => 'أداء الصلوات في المسجد النبوي والقيام، وإفطار جماعي أيام الإقامة في المدينة.',
	),
	array(
		'title' => 'العودة إلى مكة لاستكمال الاعتكاف',
		'city'  => 'مكة المكرمة',
		'desc'  => 'العودة إلى مكة المكرمة للانتظام في برنامج العشر الأواخر وموائد الإفطار في الفندق.',
	),
	array(
		'title' => 'العشر الأواخر والاعتكاف',
		'city'  => 'مكة المكرمة',
		'desc'  => 'الاعتكاف والعمرات في العشر الأواخر من رمضان، والسهر على الطاعة وقيام ليالي الوتر.',
	),
	array(
		'title' => 'طواف الوداع والاستعداد للسفر',
		'city'  => 'مكة المكرمة',
		'desc'  => 'أداء طواف الوداع وترتيب الحقائب والاستعداد للعودة بعد إتمام أيام الرحلة الطويلة.',
	),
	array(
		'title' => 'العودة إلى مصر',
		'city'  => 'القاهرة',
		'desc'  => 'السفر من مطار جدة أو مطار المدينة إلى مطار القاهرة والعودة إلى نقطة الخروج نفسها.',
	),
) );

define( 'HU_FIXED_INCLUDES', array(
	'تذكرة طيران ذهاب وعودة',
	'إقامة فندقية 4 نجوم',
	'تأشيرة العمرة',
	'رسوم المطوف وأوضاع النقل',
	'وجبات',
	'مرشد شرعي مرافق',
) );

define( 'HU_FIXED_EXCLUDES', array(
	'المصروفات الشخصية',
	'مصاريف الأمتعة الزائدة',
	'الهدايا والتسوق',
) );

/* -------------------------------------------------------------
 * 1) إعدادات الثيم الأساسية
 * ------------------------------------------------------------*/
function hu_setup() {
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script' ) );
	add_theme_support( 'custom-logo', array(
		'height'      => 80,
		'width'       => 220,
		'flex-height' => true,
		'flex-width'  => true,
	) );

	register_nav_menus( array(
		'primary' => 'القائمة الرئيسية',
		'footer'  => 'قائمة الفوتر',
	) );

	load_theme_textdomain( 'hajj-umrah', get_template_directory() . '/languages' );
}
add_action( 'after_setup_theme', 'hu_setup' );


/* -------------------------------------------------------------
 * 2) إضافة الأنماط والسكربتات
 * ------------------------------------------------------------*/
function hu_scripts() {
	wp_enqueue_style( 'hu-fonts', 'https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap', array(), HU_VERSION );
	wp_enqueue_style( 'hu-style', get_stylesheet_uri(), array( 'hu-fonts' ), HU_VERSION );
	wp_enqueue_style( 'hu-main', get_template_directory_uri() . '/assets/css/main.css', array( 'hu-style' ), HU_VERSION );

	wp_enqueue_script( 'hu-main', get_template_directory_uri() . '/assets/js/main.js', array(), HU_VERSION, true );

	if ( is_singular( 'trip' ) ) {
		wp_enqueue_script( 'hu-trip', get_template_directory_uri() . '/assets/js/trip.js', array(), HU_VERSION, true );
	}

	if ( is_front_page() || is_post_type_archive( 'trip' ) ) {
		wp_enqueue_script( 'hu-filter', get_template_directory_uri() . '/assets/js/filter.js', array(), HU_VERSION, true );
	}
}
add_action( 'wp_enqueue_scripts', 'hu_scripts' );


/* -------------------------------------------------------------
 * 3) نوع الرحلة المخصص (Custom Post Type)
 * ------------------------------------------------------------*/
function hu_register_trip_cpt() {
	register_post_type( 'trip', array(
		'labels' => array(
			'name'               => 'الرحلات',
			'singular_name'      => 'رحلة',
			'menu_name'          => 'رحلات الحج والعمرة',
			'add_new'            => 'إضافة رحلة',
			'add_new_item'       => 'إضافة رحلة جديدة',
			'edit_item'          => 'تعديل الرحلة',
			'new_item'           => 'رحلة جديدة',
			'view_item'          => 'عرض الرحلة',
			'search_items'       => 'بحث في الرحلات',
			'not_found'          => 'لا توجد رحلات',
			'not_found_in_trash' => 'لا توجد رحلات محذوفة',
		),
		'public'       => true,
		'has_archive'  => true,
		'menu_icon'    => 'dashicons-palmtree',
		'rewrite'      => array( 'slug' => 'trips' ),
		'supports'     => array( 'title', 'editor', 'thumbnail', 'excerpt' ),
		'show_in_rest' => true,
	) );

	register_taxonomy( 'trip_type', 'trip', array(
		'labels' => array(
			'name'          => 'نوع الرحلة',
			'singular_name' => 'نوع الرحلة',
			'all_items'     => 'كل الأنواع',
			'add_new_item'  => 'إضافة نوع',
		),
		'hierarchical'      => true,
		'public'            => true,
		'show_in_rest'      => true,
		'show_admin_column' => true,
		'rewrite'           => array( 'slug' => 'trip-type' ),
	) );
}
add_action( 'init', 'hu_register_trip_cpt' );

function hu_demo_types() {
	$terms = array(
		'حج'           => 'hajj',
		'عمرة'         => 'umrah',
		'عمرة رمضان' => 'ramadan',
	);
	foreach ( $terms as $name => $slug ) {
		if ( ! get_term_by( 'slug', $slug, 'trip_type' ) ) {
			wp_insert_term( $name, 'trip_type', array( 'slug' => $slug ) );
		}
	}
}
add_action( 'init', 'hu_demo_types' );

function hu_get_trip_types() {
	$types = get_terms( array(
		'taxonomy'   => 'trip_type',
		'hide_empty' => false,
	) );
	if ( is_wp_error( $types ) || empty( $types ) ) {
		return array();
	}
	return $types;
}

function hu_get_or_create_trip_type( $slug, $label ) {
	$term = get_term_by( 'slug', $slug, 'trip_type' );
	if ( $term ) {
		return (int) $term->term_id;
	}
	$inserted = wp_insert_term( $label, 'trip_type', array( 'slug' => $slug ) );
	return is_wp_error( $inserted ) ? 0 : (int) $inserted['term_id'];
}

function hu_trip_is_ramadan( $post_id ) {
	$terms = get_the_terms( $post_id, 'trip_type' );
	if ( is_array( $terms ) ) {
		foreach ( $terms as $t ) {
			if ( 'ramadan' === $t->slug ) {
				return true;
			}
		}
	}
	return false;
}


/* -------------------------------------------------------------
 * 4) الحقول المخصصة للرحلات (Meta Boxes)
 * ------------------------------------------------------------*/
function hu_register_meta_boxes() {
	add_meta_box(
		'hu_trip_basics',
		'بيانات الرحلة الأساسية',
		'hu_trip_basics_cb',
		'trip',
		'normal',
		'high'
	);
	add_meta_box(
		'hu_trip_itinerary',
		'برنامج السير (من الخروج حتى العودة) — رتب الخطوات بالترتيب من فوق لتحت',
		'hu_trip_itinerary_cb',
		'trip',
		'normal',
		'high'
	);
	add_meta_box(
		'hu_trip_includes',
		'ما تشمله الرحلة والاستثناءات',
		'hu_trip_includes_cb',
		'trip',
		'normal',
		'default'
	);
}
add_action( 'add_meta_boxes', 'hu_register_meta_boxes' );

function hu_save_meta( $post_id ) {
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}
	if ( ! isset( $_POST['hu_trip_meta_nonce'] ) || ! wp_verify_nonce( $_POST['hu_trip_meta_nonce'], 'hu_trip_meta' ) ) {
		return;
	}
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	// الأساسيات (نصية/أرقام)
	$number_fields = array( 'hu_price', 'hu_duration', 'hu_departure', 'hu_return', 'hu_capacity', 'hu_remaining' );
	foreach ( $number_fields as $field ) {
		if ( isset( $_POST[ $field ] ) ) {
			update_post_meta( $post_id, '_' . $field, sanitize_text_field( wp_unslash( $_POST[ $field ] ) ) );
		}
	}

	// وسيلة النقل
	if ( isset( $_POST['hu_transport'] ) ) {
		update_post_meta( $post_id, '_hu_transport', sanitize_text_field( wp_unslash( $_POST['hu_transport'] ) ) );
	}

	// حالة التوفر
	if ( isset( $_POST['hu_active'] ) ) {
		update_post_meta( $post_id, '_hu_active', '1' );
	} else {
		update_post_meta( $post_id, '_hu_active', '0' );
	}

	// برنامج السير: مصفوفة خطوات
	if ( isset( $_POST['hu_itinerary'] ) && is_array( $_POST['hu_itinerary'] ) ) {
		$steps = array();
		foreach ( $_POST['hu_itinerary'] as $step ) {
			$step = wp_parse_args( $step, array( 'title' => '', 'desc' => '', 'city' => '' ) );
			if ( '' === trim( $step['title'] ) && '' === trim( $step['desc'] ) ) {
				continue; // نتخطى الصفوف الفارغة
			}
			$steps[] = array(
				'title' => sanitize_text_field( wp_unslash( $step['title'] ) ),
				'city'  => sanitize_text_field( wp_unslash( $step['city'] ) ),
				'desc'  => sanitize_textarea_field( wp_unslash( $step['desc'] ) ),
			);
		}
		update_post_meta( $post_id, '_hu_itinerary', $steps );
	}

	// ما تشمله وما لا تشمله
	if ( isset( $_POST['hu_includes'] ) ) {
		update_post_meta( $post_id, '_hu_includes', array_map( 'sanitize_text_field', wp_unslash( $_POST['hu_includes'] ) ) );
	} else {
		update_post_meta( $post_id, '_hu_includes', array() );
	}
	if ( isset( $_POST['hu_excludes'] ) ) {
		update_post_meta( $post_id, '_hu_excludes', array_map( 'sanitize_text_field', wp_unslash( $_POST['hu_excludes'] ) ) );
	} else {
		update_post_meta( $post_id, '_hu_excludes', array() );
	}

	// المدة ثابتة تلقائياً: 15 يوم للرحلات العادية، 40 يوم لعمرة رمضان
	update_post_meta( $post_id, '_hu_duration', hu_trip_is_ramadan( $post_id ) ? HU_RAMADAN_DURATION : HU_FIXED_DURATION );
}
add_action( 'save_post_trip', 'hu_save_meta' );

function hu_trip_basics_cb( $post ) {
	wp_nonce_field( 'hu_trip_meta', 'hu_trip_meta_nonce' );

	$price     = get_post_meta( $post->ID, '_hu_price', true );
	$departure = get_post_meta( $post->ID, '_hu_departure', true );
	$return    = get_post_meta( $post->ID, '_hu_return', true );
	$transport = get_post_meta( $post->ID, '_hu_transport', true );
	$capacity  = get_post_meta( $post->ID, '_hu_capacity', true );
	$remaining = get_post_meta( $post->ID, '_hu_remaining', true );
	$active    = get_post_meta( $post->ID, '_hu_active', true );

	?>
	<table class="form-table">
		<tr>
			<th><label for="hu_price">السعر (بالجنيه)</label></th>
			<td><input type="text" id="hu_price" name="hu_price" class="regular-text" value="<?php echo esc_attr( $price ); ?>" placeholder="مثال: 45000"></td>
		</tr>
		<tr>
			<th><label>مدة الرحلة</label></th>
			<td>
				<input type="text" class="regular-text" value="<?php echo esc_attr( hu_trip_is_ramadan( $post->ID ) ? HU_RAMADAN_DURATION : HU_FIXED_DURATION ); ?>" disabled="disabled">
				<p class="description">مدة ثابتة تلقائياً: 15 يوم للرحلات العادية، و40 يوم لعمرة رمضان.</p>
			</td>
		</tr>
		<tr>
			<th><label for="hu_departure">تاريخ الخروج</label></th>
			<td><input type="date" id="hu_departure" name="hu_departure" value="<?php echo esc_attr( $departure ); ?>"></td>
		</tr>
		<tr>
			<th><label for="hu_return">تاريخ العودة</label></th>
			<td><input type="date" id="hu_return" name="hu_return" value="<?php echo esc_attr( $return ); ?>"></td>
		</tr>
		<tr>
			<th><label for="hu_transport">وسيلة النقل</label></th>
			<td>
				<select id="hu_transport" name="hu_transport">
					<option value="طيران" <?php selected( $transport, 'طيران' ); ?>>طيران</option>
					<option value="أرضي (باص)" <?php selected( $transport, 'أرضي (باص)' ); ?>>أرضي (باص)</option>
					<option value="طيران وأرضي" <?php selected( $transport, 'طيران وأرضي' ); ?>>طيران وأرضي</option>
					<option value="سيارة خاصة" <?php selected( $transport, 'سيارة خاصة' ); ?>>سيارة خاصة</option>
				</select>
			</td>
		</tr>
		<tr>
			<th><label for="hu_capacity">الطاقة الاستيعابية</label></th>
			<td><input type="number" id="hu_capacity" name="hu_capacity" value="<?php echo esc_attr( $capacity ); ?>" placeholder="مثال: 45"></td>
		</tr>
		<tr>
			<th><label for="hu_remaining">الأماكن المتبقية</label></th>
			<td><input type="number" id="hu_remaining" name="hu_remaining" value="<?php echo esc_attr( $remaining ); ?>" placeholder="مثال: 12"></td>
		</tr>
		<tr>
			<th>حالة الرحلة</th>
			<td>
				<label>
					<input type="checkbox" name="hu_active" value="1" <?php checked( $active, '1' ); ?>>
					الرحلة متاحة للحجز ومُعروضة على الموقع
				</label>
			</td>
		</tr>
	</table>
	<?php
}

function hu_trip_itinerary_cb( $post ) {
	$itinerary = get_post_meta( $post->ID, '_hu_itinerary', true );
	if ( ! is_array( $itinerary ) ) {
		$itinerary = array();
	}
	?>
	<p>أضف خطوات الرحلة بالترتيب الصحيح، أول خطوة = نقطة الانطلاق، واخر خطوة = العودة إلى نقطة الخروج.</p>
	<div class="hu-itinerary-block" data-index="<?php echo count( $itinerary ); ?>">
		<div class="hu-itinerary-wrap">
			<?php if ( empty( $itinerary ) ) : ?>
				<div class="hu-step" data-index="0">
					<?php hu_itinerary_row_html( 0, array() ); ?>
				</div>
			<?php else : ?>
				<?php foreach ( $itinerary as $i => $step ) : ?>
					<div class="hu-step" data-index="<?php echo (int) $i; ?>">
						<?php hu_itinerary_row_html( $i, $step ); ?>
					</div>
				<?php endforeach; ?>
			<?php endif; ?>
		</div>
		<button type="button" class="button button-primary hu-add-step">+ إضافة خطوة جديدة</button>
		<button type="button" class="button hu-reorder-steps">ترتيب الخطوات تصاعدياً</button>
	</div>
	<?php
}

function hu_itinerary_row_html( $i, $step ) {
	$step = wp_parse_args( $step, array( 'title' => '', 'city' => '', 'desc' => '' ) );
	?>
	<div class="hu-step-inner" style="border:1px solid #dcdcde;padding:10px;margin-bottom:10px;background:#f9f9f9;">
		<p style="margin-top:0">
			<strong>الخطوة #<span class="hu-step-label"><?php echo (int) $i + 1; ?></span></strong>
		</p>
		<p>
			<label>عنوان الخطوة (مثال: الوصول إلى مكة المكرمة)</label>
			<input type="text" name="hu_itinerary[<?php echo (int) $i; ?>][title]" class="widefat" value="<?php echo esc_attr( $step['title'] ); ?>">
		</p>
		<p>
			<label>المدينة / الموقع</label>
			<input type="text" name="hu_itinerary[<?php echo (int) $i; ?>][city]" class="widefat" value="<?php echo esc_attr( $step['city'] ); ?>" placeholder="مثال: مكة المكرمة">
		</p>
		<p>
			<label>تفاصيل الخطوة</label>
			<textarea name="hu_itinerary[<?php echo (int) $i; ?>][desc]" class="widefat" rows="3"><?php echo esc_textarea( $step['desc'] ); ?></textarea>
		</p>
		<p>
			<button type="button" class="button hu-remove-step">حذف الخطوة</button>
			<button type="button" class="button hu-move-up">▲ لأعلى</button>
			<button type="button" class="button hu-move-down">▼ لأسفل</button>
		</p>
	</div>
	<?php
}

function hu_trip_includes_cb( $post ) {
	$includes = get_post_meta( $post->ID, '_hu_includes', true );
	$excludes = get_post_meta( $post->ID, '_hu_excludes', true );
	$includes = is_array( $includes ) ? $includes : array();
	$excludes = is_array( $excludes ) ? $excludes : array();
	hu_repeater_field( 'hu_includes', 'يشمل السعر', $includes );
	hu_repeater_field( 'hu_excludes', 'لا يشمل السعر', $excludes );
}

function hu_repeater_field( $name, $label, $items ) {
	echo '<div style="margin-bottom:20px;">';
	echo '<h3 style="margin:5px 0;">' . esc_html( $label ) . '</h3>';
	echo '<div class="hu-repeater" data-name="' . esc_attr( $name ) . '">';
	$items = array_values( $items );
	if ( empty( $items ) ) {
		$items = array( '' );
	}
	foreach ( $items as $i => $item ) {
		echo '<div class="hu-repeater-row" style="margin-bottom:5px;">';
		echo '<input type="text" name="' . esc_attr( $name ) . '[' . (int) $i . ']" class="widefat" value="' . esc_attr( $item ) . '">';
		echo '</div>';
	}
	echo '</div>';
	echo '<button type="button" class="button hu-add-row">+ إضافة فقرة</button>';
	echo '</div>';
}

function hu_tel_href( $phone = '' ) {
	if ( '' === $phone ) {
		$phone = get_option( 'hu_phone', '' );
	}
	return 'tel:' . preg_replace( '/[^\d+]/', '', $phone );
}

function hu_wa_href( $whats = '' ) {
	if ( '' === $whats ) {
		$whats = get_option( 'hu_whatsapp', '' );
	}
	$number = preg_replace( '/[^\d]/', '', $whats );
	if ( '' === $number ) {
		return '';
	}
	return 'https://wa.me/' . $number . '?text=' . rawurlencode( 'أهلًا، أرغب في الاستفسار عن رحلات الحج والعمرة المتاحة حاليًا' );
}


/* -------------------------------------------------------------
 * 5) صفحة إعدادات الشركة
 * ------------------------------------------------------------*/
function hu_register_settings_page() {
	add_menu_page(
		'بيانات موقع الحج والعمرة',
		'بيانات الموقع',
		'manage_options',
		'hu-settings',
		'hu_settings_page_cb',
		'dashicons-admin-generic',
		30
	);
}
add_action( 'admin_menu', 'hu_register_settings_page' );

function hu_settings_page_cb() {
	if ( isset( $_POST['hu_save_settings'] ) && check_admin_referer( 'hu_settings' ) ) {
		$fields = array( 'hu_company', 'hu_phone', 'hu_whatsapp', 'hu_email', 'hu_address', 'hu_fb', 'hu_hero_title', 'hu_hero_sub' );
		foreach ( $fields as $field ) {
			if ( isset( $_POST[ $field ] ) ) {
				update_option( $field, sanitize_text_field( wp_unslash( $_POST[ $field ] ) ) );
			}
		}
		echo '<div class="notice notice-success"><p>تم حفظ البيانات.</p></div>';
	}
	?>
	<div class="wrap">
		<h1>بيانات الشركة والموقع</h1>
		<form method="post">
			<?php wp_nonce_field( 'hu_settings' ); ?>
			<table class="form-table">
				<?php
				$text_fields = array(
					'hu_company'     => 'اسم الشركة',
					'hu_phone'       => 'رقم الهاتف',
					'hu_whatsapp'    => 'رقم الواتساب (بصيغة دولية مثال: 201012345678)',
					'hu_email'       => 'البريد الإلكتروني',
					'hu_address'     => 'العنوان',
					'hu_fb'          => 'رابط صفحة فيسبوك',
					'hu_hero_title'   => 'العنوان الرئيسي في الصفحة الرئيسية',
					'hu_hero_sub'     => 'النص التمهيدي في الصفحة الرئيسية',
				);
				foreach ( $text_fields as $id => $label ) {
					$val = get_option( $id, '' );
					echo '<tr><th><label for="' . esc_attr( $id ) . '">' . esc_html( $label ) . '</label></th>';
					echo '<td><input type="text" id="' . esc_attr( $id ) . '" name="' . esc_attr( $id ) . '" class="regular-text" value="' . esc_attr( $val ) . '"></td></tr>';
				}
				?>
			</table>
			<?php submit_button( 'حفظ البيانات', 'primary', 'hu_save_settings' ); ?>
		</form>
	</div>
	<?php
}


/* -------------------------------------------------------------
 * 5.5) إضافة رحلة سريعة — أبسط طريقة لإضافة رحلة تظهر فوراً
 * ------------------------------------------------------------*/
function hu_register_quick_trip_menu() {
	add_submenu_page(
		'edit.php?post_type=trip',
		'إضافة رحلة سريعة',
		'➕ إضافة رحلة',
		'manage_options',
		'hu-add-trip',
		'hu_quick_trip_page_cb'
	);
}
add_action( 'admin_menu', 'hu_register_quick_trip_menu' );

/* -------------------------------------------------------------
 * كل تعديل / إضافة للرحلات بيتم من صفحة "إضافة/تعديل رحلة" فقط
 * ------------------------------------------------------------*/
function hu_edit_trip_url( $post_id ) {
	return admin_url( 'admin.php?page=hu-add-trip&edit=' . (int) $post_id );
}

// أي محاولة لفتح محرر الرحلة الافتراضي (تعديل أو إضافة) بتتحول فوراً لصفحتنا المخصصة
function hu_redirect_trip_editor() {
	global $pagenow;
	if ( 'post-new.php' === $pagenow ) {
		if ( 'trip' === ( $_GET['post_type'] ?? '' ) && current_user_can( 'manage_options' ) ) {
			wp_safe_redirect( admin_url( 'admin.php?page=hu-add-trip' ) );
			exit;
		}
		return;
	}
	if ( 'post.php' !== $pagenow || ! isset( $_GET['post'] ) || ! isset( $_GET['action'] ) || 'edit' !== $_GET['action'] ) {
		return;
	}
	$post_id = (int) $_GET['post'];
	if ( 'trip' !== get_post_type( $post_id ) || ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}
	wp_safe_redirect( hu_edit_trip_url( $post_id ) );
	exit;
}
add_action( 'admin_init', 'hu_redirect_trip_editor' );

// إخفاء "إضافة رحلة جديدة" من قايمة الرحلات في لوحة التحكم
function hu_hide_trip_wp_editor() {
	remove_submenu_page( 'edit.php?post_type=trip', 'post-new.php?post_type=trip' );
}
add_action( 'admin_menu', 'hu_hide_trip_wp_editor', 999 );

// روابط تعديل الرحلات في أي مكان بالووردبريس توصل لصفحتنا
function hu_edit_trip_link_filter( $link, $post_id, $context ) {
	if ( 'trip' === get_post_type( $post_id ) ) {
		return admin_url( 'admin.php?page=hu-add-trip&edit=' . (int) $post_id );
	}
	return $link;
}
add_filter( 'get_edit_post_link', 'hu_edit_trip_link_filter', 10, 3 );

// قايمة الرحلات: التعديل لصفحتنا، وبدون Quick Edit / Bulk Edit
function hu_trip_row_actions( $actions, $post ) {
	if ( 'trip' !== $post->post_type ) {
		return $actions;
	}
	if ( isset( $actions['edit'] ) ) {
		$actions['edit'] = '<a href="' . esc_url( hu_edit_trip_url( $post->ID ) ) . '">تعديل</a>';
	}
	unset( $actions['inline hide-if-no-js'] );
	return $actions;
}
add_filter( 'post_row_actions', 'hu_trip_row_actions', 10, 2 );

function hu_trip_bulk_actions( $actions ) {
	unset( $actions['edit'] );
	return $actions;
}
add_filter( 'bulk_actions-edit-trip', 'hu_trip_bulk_actions' );

// إخفاء زرار "إضافة رحلة" بالنماذج القديمة + رسالة توضيحية في قايمة الرحلات
function hu_trip_list_css() {
	global $pagenow;
	if ( 'edit.php' !== $pagenow || 'trip' !== ( $_GET['post_type'] ?? '' ) ) {
		return;
	}
	?>
	<style>.page-title-action{display:none!important;}</style>
	<div class="notice notice-info" style="margin:10px 0 -10px;">
		<p>🖊️ كل إضافة أو تعديل للرحلات بيتم من صفحة <a href="<?php echo esc_url( admin_url( 'admin.php?page=hu-add-trip' ) ); ?>"><strong>➕ إضافة / تعديل رحلة</strong></a>.</p>
	</div>
	<?php
}
add_action( 'admin_head', 'hu_trip_list_css' );

function hu_admin_itinerary_block( $steps ) {
	echo '<div class="hu-itinerary-block" data-index="' . count( $steps ) . '">';
	echo '<div class="hu-itinerary-wrap">';
	foreach ( $steps as $i => $step ) {
		echo '<div class="hu-step" data-index="' . (int) $i . '">';
		hu_itinerary_row_html( $i, $step );
		echo '</div>';
	}
	echo '</div>';
	echo '<button type="button" class="button button-primary hu-add-step">+ إضافة خطوة جديدة</button>';
	echo '<button type="button" class="button hu-reorder-steps">ترتيب الخطوات تصاعدياً</button>';
	echo '</div>';
}

function hu_admin_create_trip( $type_slug, $name, $price, $departure, $default_itinerary, $return_days, $duration_label, $edit_id = 0 ) {
	$type_slug   = sanitize_key( $type_slug );
	$type_labels = array(
		'hajj'    => 'الحج',
		'umrah'   => 'العمرة',
		'ramadan' => 'عمرة رمضان',
	);
	$type_label  = isset( $type_labels[ $type_slug ] ) ? $type_labels[ $type_slug ] : 'العمرة';

	$content = sanitize_textarea_field( wp_unslash( $_POST['hu_qt_desc'] ?? '' ) );

	if ( $edit_id ) {
		$update = wp_update_post( array(
			'ID'           => (int) $edit_id,
			'post_title'   => sanitize_text_field( $name ),
			'post_content' => $content,
		) );
		if ( is_wp_error( $update ) ) {
			return array( 0, $update->get_error_message() );
		}
		$post_id = (int) $edit_id;
	} else {
		$post_id = wp_insert_post( array(
			'post_type'    => 'trip',
			'post_status'  => 'publish',
			'post_title'   => sanitize_text_field( $name ),
			'post_content' => $content,
		) );
		if ( is_wp_error( $post_id ) ) {
			return array( 0, $post_id->get_error_message() );
		}
	}

	update_post_meta( $post_id, '_hu_price', sanitize_text_field( $price ) );
	update_post_meta( $post_id, '_hu_departure', sanitize_text_field( $departure ) );
	update_post_meta( $post_id, '_hu_duration', $duration_label );
	update_post_meta( $post_id, '_hu_transport', HU_FIXED_TRANSPORT );
	update_post_meta( $post_id, '_hu_capacity', (string) HU_FIXED_CAPACITY );
	update_post_meta( $post_id, '_hu_remaining', (string) HU_FIXED_CAPACITY );
	update_post_meta( $post_id, '_hu_return', date( 'Y-m-d', strtotime( $departure . ' +' . (int) $return_days . ' days' ) ) );

	$steps = array();
	if ( isset( $_POST['hu_itinerary'] ) && is_array( $_POST['hu_itinerary'] ) ) {
		foreach ( $_POST['hu_itinerary'] as $step ) {
			$step = wp_parse_args( $step, array( 'title' => '', 'city' => '', 'desc' => '' ) );
			if ( '' === trim( $step['title'] ) && '' === trim( $step['desc'] ) ) {
				continue;
			}
			$steps[] = array(
				'title' => sanitize_text_field( wp_unslash( $step['title'] ) ),
				'city'  => sanitize_text_field( wp_unslash( $step['city'] ) ),
				'desc'  => sanitize_textarea_field( wp_unslash( $step['desc'] ) ),
			);
		}
	}
	update_post_meta( $post_id, '_hu_itinerary', empty( $steps ) ? $default_itinerary : $steps );

	// السعر يشمل / لا يشمل (لو فاضية تتحفظ القوائم الافتراضية)
	$hu_includes = array();
	if ( isset( $_POST['hu_includes'] ) && is_array( $_POST['hu_includes'] ) ) {
		$hu_includes = array_values( array_filter( array_map( 'sanitize_text_field', wp_unslash( $_POST['hu_includes'] ) ) ) );
	}
	update_post_meta( $post_id, '_hu_includes', array() === $hu_includes ? HU_FIXED_INCLUDES : $hu_includes );

	$hu_excludes = array();
	if ( isset( $_POST['hu_excludes'] ) && is_array( $_POST['hu_excludes'] ) ) {
		$hu_excludes = array_values( array_filter( array_map( 'sanitize_text_field', wp_unslash( $_POST['hu_excludes'] ) ) ) );
	}
	update_post_meta( $post_id, '_hu_excludes', array() === $hu_excludes ? HU_FIXED_EXCLUDES : $hu_excludes );

	update_post_meta( $post_id, '_hu_active', '1' );

	$term_id = hu_get_or_create_trip_type( $type_slug, $type_label );
	if ( $term_id ) {
		wp_set_object_terms( $post_id, array( $term_id ), 'trip_type' );
	}

	return array( (int) $post_id, '' );
}

function hu_quick_trip_page_cb() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}

	if ( isset( $_GET['hu_del'] ) ) {
		$del_id = (int) $_GET['hu_del'];
		if ( check_admin_referer( 'hu_del_trip_' . $del_id ) ) {
			wp_delete_post( $del_id, true );
			wp_safe_redirect( admin_url( 'admin.php?page=hu-add-trip&hu_deleted=1' ) );
			exit;
		}
	}

	$notice = '';
	if ( isset( $_POST['hu_qt_submit'] ) || isset( $_POST['hu_ramadan_submit'] ) ) {
		if ( ! check_admin_referer( 'hu_quick_trip', 'hu_qt_nonce' ) ) {
			$notice = '<div class="notice notice-error"><p>حدث خطأ في التحقق، حاول مرة أخرى.</p></div>';
		} else {
			$is_ramadan = isset( $_POST['hu_ramadan_submit'] );
			$edit_id    = (int) ( $_POST['hu_edit_id'] ?? 0 );
			$name       = sanitize_text_field( wp_unslash( $_POST[ $is_ramadan ? 'hu_ram_name' : 'hu_qt_name' ] ?? '' ) );
			$departure  = sanitize_text_field( wp_unslash( $_POST[ $is_ramadan ? 'hu_ram_departure' : 'hu_qt_departure' ] ?? '' ) );

			if ( '' === trim( $name ) ) {
				$notice = '<div class="notice notice-error"><p>اكتب اسم الرحلة أولاً.</p></div>';
			} elseif ( '' === $departure ) {
				$notice = '<div class="notice notice-error"><p>حدد تاريخ الخروج (مهم لترتيب الرحلات على الموقع).</p></div>';
			} else {
				$price       = sanitize_text_field( wp_unslash( $_POST[ $is_ramadan ? 'hu_ram_price' : 'hu_qt_price' ] ?? '' ) );
				$type        = $is_ramadan ? 'ramadan' : ( ( 'hajj' === ( $_POST['hu_qt_type'] ?? '' ) ) ? 'hajj' : 'umrah' );
				$defaults    = $is_ramadan ? HU_FIXED_ITINERARY_RAMADAN : HU_FIXED_ITINERARY;
				$return_days = $is_ramadan ? HU_RAMADAN_RETURN_DAYS : HU_FIXED_RETURN_DAYS;
				$duration    = $is_ramadan ? HU_RAMADAN_DURATION : HU_FIXED_DURATION;

				list( $post_id, $err ) = hu_admin_create_trip( $type, $name, $price, $departure, $defaults, $return_days, $duration, $edit_id );

				if ( $post_id ) {
					if ( $edit_id ) {
						wp_safe_redirect( admin_url( 'admin.php?page=hu-add-trip&edit=' . $post_id . '&hu_updated=1' ) );
					} else {
						wp_safe_redirect( admin_url( 'admin.php?page=hu-add-trip&hu_created=' . $post_id ) );
					}
					exit;
				}
				$notice = '<div class="notice notice-error"><p>فشل حفظ الرحلة: ' . esc_html( $err ) . '</p></div>';
			}
		}
	}

	// بيانات الرحلة المعروضة للتعديل (تُقرأ من قاعدة البيانات)
	$editing         = 0;
	$edit_type       = '';
	$edit_title      = '';
	$edit_price      = '';
	$edit_departure  = '';
	$edit_itinerary  = array();
	$edit_includes   = array();
	$edit_excludes   = array();
	if ( isset( $_GET['edit'] ) ) {
		$candidate = (int) $_GET['edit'];
		if ( $candidate && 'trip' === get_post_type( $candidate ) && current_user_can( 'edit_post', $candidate ) ) {
			$editing        = $candidate;
			$edit_title     = get_the_title( $editing );
			$edit_price     = get_post_meta( $editing, '_hu_price', true );
			$edit_departure = get_post_meta( $editing, '_hu_departure', true );
			$edit_itinerary = get_post_meta( $editing, '_hu_itinerary', true );
			$edit_includes  = get_post_meta( $editing, '_hu_includes', true );
			$edit_excludes  = get_post_meta( $editing, '_hu_excludes', true );
			$edit_itinerary = is_array( $edit_itinerary ) ? $edit_itinerary : array();
			$edit_includes  = is_array( $edit_includes ) ? $edit_includes : array();
			$edit_excludes  = is_array( $edit_excludes ) ? $edit_excludes : array();
			if ( hu_trip_is_ramadan( $editing ) ) {
				$edit_type = 'ramadan';
			} else {
				$et        = wp_get_post_terms( $editing, 'trip_type', array( 'fields' => 'slugs' ) );
				$edit_type = ( in_array( 'hajj', $et, true ) && ! in_array( 'umrah', $et, true ) ) ? 'hajj' : 'umrah';
			}
		}
	}
	$normal_steps   = ( $editing && 'ramadan' !== $edit_type && $edit_itinerary ) ? $edit_itinerary : HU_FIXED_ITINERARY;
	$ramadan_steps  = ( $editing && 'ramadan' === $edit_type && $edit_itinerary ) ? $edit_itinerary : HU_FIXED_ITINERARY_RAMADAN;
	$inc_display    = ( $editing && 'ramadan' !== $edit_type && $edit_includes ) ? $edit_includes : HU_FIXED_INCLUDES;
	$exc_display    = ( $editing && 'ramadan' !== $edit_type && $edit_excludes ) ? $edit_excludes : HU_FIXED_EXCLUDES;
	?>
	<div class="wrap">
		<h1><?php echo $editing ? '✏️ تعديل الرحلة' : '➕ إضافة رحلة سريعة'; ?></h1>
		<?php if ( $editing ) : ?>
			<div style="background:#fff8e5;border:1px solid #f0c33c;border-radius:8px;padding:12px 16px;max-width:800px;margin-bottom:14px;">
				<strong>أنت بتعدل حالياً:</strong> <?php echo esc_html( $edit_title ); ?>
				<?php if ( 'ramadan' === $edit_type ) : ?>
					— <strong>🌙 عمرة رمضان (40 يوم)</strong>
				<?php else : ?>
					— رحلة عادية (15 يوم)
				<?php endif; ?>
				— <a href="<?php echo esc_url( admin_url( 'admin.php?page=hu-add-trip' ) ); ?>">اضغط هنا لإضافة رحلة جديدة بدلاً منها</a>
			</div>
		<?php else : ?>
			<p style="color:#6b7280;max-width:800px;">كل رحلة بتظهر على الموقع فوراً بنفس الثوابت الآتية: <strong>المدة 15 يوم للرحلات العادية، و40 يوم لعمرة رمضان</strong> — النقل طيران — السعة 45 شخص. العودة بتتحسب تلقائياً من تاريخ الخروج.<br>
			<em>كل تعديل أو إضافة للرحلات بيتم من هنا فقط، ومفيش محرر تاني.</em></p>
		<?php endif; ?>

		<?php echo $notice; // phpcs:ignore ?>
		<?php if ( isset( $_GET['hu_deleted'] ) ) : ?>
			<div class="notice notice-success"><p>تم حذف الرحلة.</p></div>
		<?php elseif ( isset( $_GET['hu_updated'] ) ) : ?>
			<div class="notice notice-success"><p><strong>✅ تم حفظ تعديلات الرحلة ونشرها على الموقع فوراً.</strong>
				<a href="<?php echo esc_url( get_permalink( (int) $_GET['hu_updated'] ) ); ?>" target="_blank">عرضها في الموقع</a></p></div>
		<?php elseif ( isset( $_GET['hu_created'] ) ) : ?>
			<div class="notice notice-success"><p><strong>✅ تمت إضافة الرحلة ونشرها على الموقع فوراً.</strong>
				<a href="<?php echo esc_url( get_permalink( (int) $_GET['hu_created'] ) ); ?>" target="_blank">عرضها في الموقع</a></p></div>
		<?php endif; ?>

		<nav class="nav-tab-wrapper" style="margin-bottom:18px;">
			<a href="#hu-tab-normal" class="nav-tab nav-tab-active" onclick="huTab(event,'hu-tab-normal')">الرحلات العادية (عمرة / حج)</a>
			<a href="#hu-tab-ramadan" class="nav-tab" onclick="huTab(event,'hu-tab-ramadan')">🌙 عمرة رمضان (40 يوم — ترتيبات ومزارات خاصة)</a>
		</nav>
		<script>
		window.huEditType = <?php echo wp_json_encode( $edit_type ); ?>;
		function huTab( e, id ) {
			e.preventDefault();
			huActivateTab( id );
		}
		function huActivateTab( id ) {
			document.querySelectorAll( '.hu-tab-panel' ).forEach( function ( p ) { p.style.display = 'none'; } );
			document.getElementById( id ).style.display = 'block';
			document.querySelectorAll( '.nav-tab' ).forEach( function ( t ) { t.classList.remove( 'nav-tab-active' ); } );
			document.querySelector( '.nav-tab[href="#' + id + '"]' ).classList.add( 'nav-tab-active' );
		}
		function huDisableForm( form, on ) {
			if ( ! form ) { return; }
			form.querySelectorAll( 'input,textarea,select,button' ).forEach( function ( el ) {
				el.disabled = on;
			} );
		}
		if ( window.huEditType === 'ramadan' ) {
			huActivateTab( 'hu-tab-ramadan' );
			huDisableForm( document.querySelector( '#hu-tab-normal form' ), true );
		} else if ( window.huEditType ) {
			huActivateTab( 'hu-tab-normal' );
			huDisableForm( document.querySelector( '#hu-tab-ramadan form' ), true );
		}
		</script>

		<!-- القسم 1: الرحلات العادية -->
		<div id="hu-tab-normal" class="hu-tab-panel" style="display:block;">
			<form method="post" style="background:#fff;padding:24px;border:1px solid #dcdcde;border-radius:8px;max-width:800px;">
				<?php wp_nonce_field( 'hu_quick_trip', 'hu_qt_nonce' ); ?>
				<input type="hidden" name="hu_edit_id" value="<?php echo (int) $editing; ?>">
				<table class="form-table" role="presentation">
					<tr>
						<th><label for="hu_qt_name">اسم الرحلة *</label></th>
						<td><input type="text" id="hu_qt_name" name="hu_qt_name" class="regular-text" style="width:100%;" required placeholder="مثال: عمرة رجب — رحلة العمرة الكبرى" value="<?php echo esc_attr( $editing && 'ramadan' !== $edit_type ? $edit_title : '' ); ?>"></td>
					</tr>
					<tr>
						<th><label for="hu_qt_price">السعر (بالجنيه)</label></th>
						<td><input type="text" id="hu_qt_price" name="hu_qt_price" class="regular-text" style="width:100%;" placeholder="مثال: 35000 — لو سبتها فاضية هتظهر (اكتب لنا)" value="<?php echo esc_attr( $editing && 'ramadan' !== $edit_type ? $edit_price : '' ); ?>"></td>
					</tr>
					<tr>
						<th><label for="hu_qt_type">نوع الرحلة</label></th>
						<td>
							<select id="hu_qt_type" name="hu_qt_type">
								<option value="umrah" <?php selected( 'umrah', $editing && 'ramadan' !== $edit_type ? $edit_type : 'umrah' ); ?>>عمرة</option>
								<option value="hajj" <?php selected( 'hajj', $editing && 'ramadan' !== $edit_type ? $edit_type : '' ); ?>>حج</option>
							</select>
						</td>
					</tr>
					<tr>
						<th><label for="hu_qt_departure">تاريخ الخروج *</label></th>
						<td>
							<input type="date" id="hu_qt_departure" name="hu_qt_departure" required value="<?php echo esc_attr( $editing && 'ramadan' !== $edit_type ? $edit_departure : '' ); ?>">
							<p class="description">مدة الرحلة 15 يوم — تاريخ العودة يُحسب تلقائياً = تاريخ الخروج + 14 يوم.</p>
						</td>
					</tr>
				</table>

				<h3 style="margin-top:30px;">📋 خط سير الرحلة</h3>
				<p style="color:#6b7280;">خط سير العادية جاهز — عدّل أي نص، اضغط <strong>حذف الخطوة</strong> لمسح خطوة، أو <strong>+ إضافة خطوة جديدة</strong>. الترتيب بالأسهم ▲ ▼.</p>
				<?php hu_admin_itinerary_block( $normal_steps ); ?>
				<p class="description" style="margin-top:10px;">المدة 15 يوم — النقل طيران — السعة 45 شخص.</p>

				<h3 style="margin-top:30px;">💵 السعر يشمل / لا يشمل</h3>
				<p style="color:#6b7280;">القوائم جاهزة بالافتراضي — عدّل أي بند أو امسحه، واضغط <strong>+ إضافة فقرة</strong> لإضافة عنصر جديد.</p>
				<?php hu_repeater_field( 'hu_includes', 'يشمل السعر', $inc_display ); ?>
				<?php hu_repeater_field( 'hu_excludes', 'لا يشمل السعر', $exc_display ); ?>

				<?php submit_button( $editing ? '💾 حفظ تعديلات الرحلة ونشرها (15 يوم)' : 'إضافة الرحلة ونشرها (15 يوم)', 'primary large', 'hu_qt_submit' ); ?>
			</form>
		</div>

		<!-- القسم 2: عمرة رمضان (منفصلة وبتفاصيل أطول) -->
		<div id="hu-tab-ramadan" class="hu-tab-panel" style="display:none;">
			<div style="background:linear-gradient(135deg,#f0f7f7,#e6f2f2);border:1px solid #9fd0ce;border-radius:8px;padding:14px 18px;max-width:800px;margin-bottom:16px;">
				<strong>🌙 قسم عمرة رمضان الخاص</strong> — رحلة منفصلة بمدة <strong>40 يوم</strong>، ببرنامج سير أطول وترتيبات ومزارات أكتر من الرحلات العادية (غار حراء، قباء، البقيع، أحد، اعتكاف العشر الأواخر، عمرات متعددة...). العودة = الخروج + 39 يوم.
			</div>
			<form method="post" style="background:#fff;padding:24px;border:1px solid #9fd0ce;border-radius:8px;max-width:800px;">
				<?php wp_nonce_field( 'hu_quick_trip', 'hu_qt_nonce' ); ?>
				<input type="hidden" name="hu_edit_id" value="<?php echo (int) $editing; ?>">
				<table class="form-table" role="presentation">
					<tr>
						<th><label for="hu_ram_name">اسم رحلة رمضان *</label></th>
						<td><input type="text" id="hu_ram_name" name="hu_ram_name" class="regular-text" style="width:100%;" required placeholder="مثال: عمرة رمضان — رحلة العمرة الكبرى" value="<?php echo esc_attr( $editing && 'ramadan' === $edit_type ? $edit_title : '' ); ?>"></td>
					</tr>
					<tr>
						<th><label for="hu_ram_price">السعر (بالجنيه)</label></th>
						<td><input type="text" id="hu_ram_price" name="hu_ram_price" class="regular-text" style="width:100%;" placeholder="مثال: 45000 — لو سبتها فاضية هتظهر (اكتب لنا)" value="<?php echo esc_attr( $editing && 'ramadan' === $edit_type ? $edit_price : '' ); ?>"></td>
					</tr>
					<tr>
						<th><label for="hu_ram_departure">تاريخ الخروج *</label></th>
						<td>
							<input type="date" id="hu_ram_departure" name="hu_ram_departure" required value="<?php echo esc_attr( $editing && 'ramadan' === $edit_type ? $edit_departure : '' ); ?>">
							<p class="description">مدة رحلة رمضان 40 يوم — تاريخ العودة يُحسب تلقائياً = تاريخ الخروج + 39 يوم.</p>
						</td>
					</tr>
				</table>

				<h3 style="margin-top:30px;">📋 برنامج السير الخاص برمضان</h3>
				<p style="color:#6b7280;">برنامج جاهز بـ 14 خطوة (ترتيبات ومزارات أكتر من العادية) — عدّل أو احذف أو ضيف أي خطوة.</p>
				<?php hu_admin_itinerary_block( $ramadan_steps ); ?>
				<p class="description" style="margin-top:10px;">المدة 40 يوم — النقل طيران — السعة 45 شخص.</p>

				<h3 style="margin-top:30px;">💵 السعر يشمل / لا يشمل</h3>
				<p style="color:#6b7280;">القوائم جاهزة بالافتراضي — عدّل أو امسح أي بند، وضيف <strong>+ إضافة فقرة</strong> حسب ترتيبات رمضان.</p>
				<?php hu_repeater_field( 'hu_includes', 'يشمل السعر', ( $editing && 'ramadan' === $edit_type && $edit_includes ) ? $edit_includes : HU_FIXED_INCLUDES ); ?>
				<?php hu_repeater_field( 'hu_excludes', 'لا يشمل السعر', ( $editing && 'ramadan' === $edit_type && $edit_excludes ) ? $edit_excludes : HU_FIXED_EXCLUDES ); ?>

				<?php submit_button( $editing ? '💾 حفظ تعديلات رحلة رمضان ونشرها (40 يوم)' : '🌙 إضافة رحلة رمضان ونشرها (40 يوم)', 'primary large', 'hu_ramadan_submit' ); ?>
			</form>
		</div>

		<h2 style="margin-top:40px;">الرحلات الحالية على الموقع</h2>
		<table class="widefat striped" style="max-width:800px;">
			<thead>
				<tr><th>الرحلة</th><th>السعر</th><th>الخروج</th><th>المدة</th><th>النوع</th><th>إجراءات</th></tr>
			</thead>
			<tbody>
				<?php
				$q = hu_get_upcoming_trips();
				if ( $q->have_posts() ) :
					while ( $q->have_posts() ) : $q->the_post();
						$t_price = get_post_meta( get_the_ID(), '_hu_price', true );
						$t_dep   = get_post_meta( get_the_ID(), '_hu_departure', true );
						$t_dur   = get_post_meta( get_the_ID(), '_hu_duration', true );
						$t_types = wp_get_post_terms( get_the_ID(), 'trip_type', array( 'fields' => 'names' ) );
						?>
						<tr>
							<td><a href="<?php echo esc_url( admin_url( 'admin.php?page=hu-add-trip&edit=' . get_the_ID() ) ); ?>"><strong><?php the_title(); ?></strong></a></td>
							<td><?php echo $t_price ? esc_html( number_format( (float) $t_price ) . ' ج.م' ) : '—'; ?></td>
							<td><?php echo $t_dep ? esc_html( $t_dep ) : '—'; ?></td>
							<td><?php echo $t_dur ? esc_html( $t_dur ) : '—'; ?></td>
							<td><?php echo $t_types ? esc_html( implode( '، ', $t_types ) ) : '—'; ?></td>
							<td>
								<a href="<?php echo esc_url( admin_url( 'admin.php?page=hu-add-trip&edit=' . get_the_ID() ) ); ?>">تعديل</a> |
								<a href="<?php echo esc_url( get_permalink() ); ?>" target="_blank">عرض</a> |
								<a href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin.php?page=hu-add-trip&hu_del=' . get_the_ID() ), 'hu_del_trip_' . get_the_ID() ) ); ?>" onclick="return confirm('متأكد إنك عايز تحذف الرحلة دي؟');">حذف</a>
							</td>
						</tr>
						<?php
					endwhile;
					wp_reset_postdata();
				else :
					?>
					<tr><td colspan="6">لا توجد رحلات بعد. اضغط "➕ إضافة رحلة سريعة" بالأعلى لإضافة أول رحلة.</td></tr>
				<?php endif; ?>
			</tbody>
		</table>
	</div>
	<?php
}


/* -------------------------------------------------------------
 * 7) نموذج الحجز / التواصل (Shortcode)
 * ------------------------------------------------------------*/
function hu_booking_shortcode() {
	ob_start();

	if ( 'POST' === $_SERVER['REQUEST_METHOD'] && isset( $_POST['hu_booking_submit'] ) ) {
		$nonce_ok = isset( $_POST['hu_booking_nonce'] ) && wp_verify_nonce( $_POST['hu_booking_nonce'], 'hu_booking' );
		$msg      = '';
		$ok       = false;

		if ( ! $nonce_ok ) {
			$msg = 'حدث خطأ في التحقق، حاول مرة أخرى.';
		} elseif ( empty( $_POST['hu_name'] ) || empty( $_POST['hu_phone'] ) ) {
			$msg = 'من فضلك أدخل الاسم ورقم الهاتف.';
		} else {
			$name    = sanitize_text_field( wp_unslash( $_POST['hu_name'] ) );
			$phone   = sanitize_text_field( wp_unslash( $_POST['hu_phone'] ) );
			$dep     = sanitize_text_field( wp_unslash( $_POST['hu_departure'] ) );
			$type    = sanitize_text_field( wp_unslash( $_POST['hu_type'] ) );
			$people  = max( 1, (int) ( $_POST['hu_people'] ?? 1 ) );
			$notes   = sanitize_textarea_field( wp_unslash( $_POST['hu_notes'] ) );

			// حفظ الطلب كـ post في ووردبريس
			$post_id = wp_insert_post( array(
				'post_type'   => 'booking',
				'post_status' => 'private',
				'post_title'  => $name . ' — ' . ( $dep ? $dep : 'بدون رحلة محددة' ),
				'post_content'=> sprintf(
					"الاسم: %s\nالهاتف: %s\nالرحلة/الموعد: %s\nنوع الرحلة: %s\nعدد الأفراد: %d\nملاحظات: %s",
					$name, $phone, $dep, $type, $people, $notes
				),
			) );
			// حفظ كل حقل في خانة مستقلة
			update_post_meta( $post_id, '_booking_name', $name );
			update_post_meta( $post_id, '_booking_phone', $phone );
			update_post_meta( $post_id, '_booking_trip', $dep );
			update_post_meta( $post_id, '_booking_type', $type );
			update_post_meta( $post_id, '_booking_people', $people );
			update_post_meta( $post_id, '_booking_notes', $notes );

			// إرسال إيميل لأدمن الموقع
			$admin_email = get_option( 'hu_email', get_option( 'admin_email' ) );
			$subject     = 'طلب حجز جديد — ' . $name;
			$body        = "طلب حجز جديد من الموقع:\n\n"
				. "الاسم: {$name}\n"
				. "الهاتف: {$phone}\n"
				. "الرحلة: {$dep}\n"
				. "النوع: {$type}\n"
				. "عدد الأفراد: {$people}\n"
				. "ملاحظات: {$notes}\n";
			wp_mail( $admin_email, $subject, $body );

			$ok  = true;
			$msg = 'تم استلام طلبك بنجاح، سنتواصل معك في أقرب وقت. جزاكم الله خيراً.';
		}

		echo '<div class="form-msg ' . ( $ok ? 'ok' : 'err' ) . '">' . esc_html( $msg ) . '</div>';
	}

	$trips = new WP_Query( array(
		'post_type' => 'trip',
		'posts_per_page' => -1,
		'post_status' => 'publish',
		'meta_query' => array( array( 'key' => '_hu_active', 'value' => '1' ) ),
		'orderby' => 'title',
		'order' => 'ASC',
	) );
	?>
	<form class="contact-form" method="post">
		<?php wp_nonce_field( 'hu_booking', 'hu_booking_nonce' ); ?>
		<div class="row2">
			<div>
				<label for="hu-name">الاسم الكامل *</label>
				<input type="text" id="hu-name" name="hu_name" required>
			</div>
			<div>
				<label for="hu-phone">رقم الهاتف *</label>
				<input type="tel" id="hu-phone" name="hu_phone" required>
			</div>
		</div>
		<div class="row2">
			<div>
				<label for="hu-departure">اختر الرحلة / الموعد</label>
				<select id="hu-departure" name="hu_departure">
					<option value="">— اختر رحلة —</option>
					<?php while ( $trips->have_posts() ) : $trips->the_post(); ?>
						<option value="<?php echo esc_attr( get_the_title() . ' — ' . get_post_meta( get_the_ID(), '_hu_departure', true ) ); ?>">
							<?php echo esc_html( get_the_title() ); ?>
						</option>
					<?php endwhile; ?>
				</select>
				<?php wp_reset_postdata(); ?>
			</div>
			<div>
				<label for="hu-type">نوع الرحلة</label>
				<select id="hu-type" name="hu_type">
					<option value="عمرة">عمرة</option>
					<option value="عمرة رمضان">عمرة رمضان</option>
					<option value="حج">حج</option>
					<option value="غير محدد">غير محدد</option>
				</select>
			</div>
		</div>
		<div>
			<label for="hu-people">عدد الأفراد</label>
			<input type="number" id="hu-people" name="hu_people" min="1" max="50" value="1">
		</div>
		<div>
			<label for="hu-notes">ملاحظاتك / استفسارك</label>
			<textarea id="hu-notes" name="hu_notes" rows="4" placeholder="اكتب أي تفاصيل تود إخبارنا بها..."></textarea>
		</div>
		<button type="submit" class="btn" name="hu_booking_submit" value="1" style="width:100%;text-align:center;">إرسال طلب الحجز</button>
	</form>
	<?php
	return ob_get_clean();
}
add_shortcode( 'hu_booking_form', 'hu_booking_shortcode' );


/* -------------------------------------------------------------
 * 8) نوع الحجوزات (Booking CPT) — يظهر في اللوحة فقط
 * ------------------------------------------------------------*/
function hu_register_booking_cpt() {
	register_post_type( 'booking', array(
		'labels' => array(
			'name'          => 'طلبات الحجز',
			'singular_name' => 'طلب حجز',
			'menu_name'     => 'طلبات الحجز',
			'search_items'  => 'بحث في الطلبات',
			'not_found'     => 'لا توجد طلبات',
		),
		'public'       => false,
		'show_ui'      => true,
		'menu_icon'    => 'dashicons-email-alt',
		'menu_position'=> 31,
		'supports'     => array( 'title', 'editor' ),
		'capability_type' => 'post',
		'map_meta_cap'    => true,
	) );
}
add_action( 'init', 'hu_register_booking_cpt' );

function hu_booking_meta_box() {
	add_meta_box(
		'hu_booking_info',
		'بيانات طلب الحجز',
		function ( $post ) {
			$rows = array(
				'اسم العميل'      => get_post_meta( $post->ID, '_booking_name', true ) ?: get_the_title( $post ),
				'رقم الهاتف'      => hu_booking_field( $post->ID, 'phone' ),
				'الرحلة / الموعد' => hu_booking_field( $post->ID, 'trip' ),
				'نوع الرحلة'      => hu_booking_field( $post->ID, 'type' ),
				'عدد الأفراد'     => hu_booking_field( $post->ID, 'people' ),
				'ملاحظات'         => hu_booking_field( $post->ID, 'notes' ),
			);
			echo '<table class="widefat striped">';
			foreach ( $rows as $label => $val ) {
				if ( 'رقم الهاتف' === $label && $val ) {
					$out = '<a href="tel:' . esc_attr( $val ) . '"><strong>' . esc_html( $val ) . '</strong></a>';
				} else {
					$out = $val ? esc_html( (string) $val ) : '—';
				}
				echo '<tr><th style="width:35%">' . esc_html( $label ) . '</th><td>' . $out . '</td></tr>';
			}
			echo '</table>';
		},
		'booking',
		'side'
	);
}
add_action( 'add_meta_boxes', 'hu_booking_meta_box' );

function hu_booking_field( $post_id, $key ) {
	if ( $key && '' !== get_post_meta( $post_id, '_booking_' . $key, true ) ) {
		return get_post_meta( $post_id, '_booking_' . $key, true );
	}

	$labels = array(
		'phone'  => 'الهاتف',
		'trip'   => 'الرحلة/الموعد',
		'type'   => 'نوع الرحلة',
		'people' => 'عدد الأفراد',
		'notes'  => 'ملاحظات',
	);
	if ( ! isset( $labels[ $key ] ) ) {
		return '';
	}

	$content = get_post_field( 'post_content', $post_id );
	foreach ( preg_split( "/\r\n|\n|\r/", (string) $content ) as $line ) {
		if ( preg_match( '/^' . preg_quote( $labels[ $key ], '/' ) . ':\s*(.*)$/u', trim( $line ), $m ) ) {
			return trim( $m[1] );
		}
	}
	return '';
}

function hu_booking_columns( $columns ) {
	$new = array();
	foreach ( $columns as $key => $label ) {
		$new[ $key ] = $label;
		if ( 'title' === $key ) {
			$new['title']   = 'الاسم / الحجز';
			$new['phone']   = 'رقم الهاتف';
			$new['type']    = 'نوع الرحلة';
			$new['trip']    = 'الرحلة / الموعد';
			$new['people']  = 'عدد الأفراد';
			$new['notes']   = 'ملاحظات';
		}
	}
	return $new;
}
add_filter( 'manage_booking_posts_columns', 'hu_booking_columns' );

function hu_booking_column_cb( $column, $post_id ) {
	$col_map = array(
		'phone'  => 'phone',
		'type'   => 'type',
		'trip'   => 'trip',
		'people' => 'people',
		'notes'  => 'notes',
	);
	if ( ! isset( $col_map[ $column ] ) ) {
		return;
	}

	$val = hu_booking_field( $post_id, $col_map[ $column ] );

	if ( 'phone' === $column ) {
		echo $val ? '<a href="tel:' . esc_attr( $val ) . '"><strong>' . esc_html( $val ) . '</strong></a>' : '—';
	} elseif ( 'notes' === $column ) {
		echo $val ? esc_html( wp_trim_words( $val, 12, '…' ) ) : '—';
	} else {
		echo $val ? esc_html( $val ) : '—';
	}
}
add_action( 'manage_booking_posts_custom_column', 'hu_booking_column_cb', 10, 2 );


/* -------------------------------------------------------------
 * 6) حلقات استعلام الرحلات (chunks)
 * ------------------------------------------------------------*/
function hu_admin_assets( $hook ) {
	wp_enqueue_script( 'hu-admin-trip', get_template_directory_uri() . '/assets/js/admin-trip.js', array(), HU_VERSION, true );
}
add_action( 'admin_enqueue_scripts', 'hu_admin_assets' );

function hu_get_upcoming_trips( $type = '' ) {
	$args = array(
		'post_type'      => 'trip',
		'posts_per_page' => -1,
		'meta_key'       => '_hu_departure',
		'orderby'        => 'meta_value',
		'order'          => 'ASC',
		'meta_query'     => array(
			array(
				'key'   => '_hu_active',
				'value' => '1',
			),
		),
	);
	if ( $type ) {
		$args['tax_query'] = array(
			array(
				'taxonomy' => 'trip_type',
				'field'    => 'slug',
				'terms'    => $type,
			),
		);
	}
	return new WP_Query( $args );
}


/* -------------------------------------------------------------
 * 7) صفحة "معاينة الموقع وتعديله" في لوحة التحكم
 * ------------------------------------------------------------*/
function hu_home_sections() {
	$default = array( 'hero', 'trips', 'why', 'cta' );
	$stored  = get_option( 'hu_home_sections', array() );
	if ( is_array( $stored ) && ! empty( $stored ) ) {
		$clean = array();
		foreach ( $stored as $s ) {
			if ( in_array( $s, $default, true ) && ! in_array( $s, $clean, true ) ) {
				$clean[] = $s;
			}
		}
		foreach ( $default as $k ) {
			if ( ! in_array( $k, $clean, true ) ) {
				$clean[] = $k;
			}
		}
		return $clean;
	}
	return $default;
}

// إخفاء شريط الأدوات داخل إطار المعاينة حتى نرى الموقع كما يراه الزائر
add_filter( 'show_admin_bar', function ( $show ) {
	if ( ! empty( $_GET['hu_preview'] ) ) {
		return false;
	}
	return $show;
} );

function hu_register_preview_menu() {
	add_menu_page(
		'معاينة الموقع وتعديله',
		'معاينة الموقع',
		'manage_options',
		'hu-site-preview',
		'hu_site_preview_cb',
		'dashicons-desktop',
		3
	);
}
add_action( 'admin_menu', 'hu_register_preview_menu' );

/**
 * أقسام الصفحة الرئيسية مع عناوين قابلة للتعديل في لوحة التحكم.
 */
function hu_preview_text_fields() {
	return array(
		'hu_company'    => array( 'sanitize_text_field', 'رحلات الحج والعمرة', 'اسم الشركة (يظهر في التذييل والهيدر)' ),
		'hu_phone'      => array( 'sanitize_text_field', '', 'رقم الهاتف (ظهور عام)' ),
		'hu_whatsapp'   => array( 'sanitize_text_field', '', 'رقم الواتساب' ),
		'hu_email'      => array( 'sanitize_email', '', 'البريد الإلكتروني' ),
		'hu_address'    => array( 'sanitize_text_field', '', 'العنوان' ),
		'hu_fb'         => array( 'esc_url_raw', '', 'رابط فيسبوك' ),
		'hu_hero_title' => array( 'sanitize_text_field', 'رحلات الحج والعمرة لكل مواسم السنة', 'عنوان الغلاف الرئيسي' ),
		'hu_hero_sub'   => array( 'sanitize_textarea_field', 'تعرّف على رحلاتنا بتفاصيل كاملة لأيام السير، من نقطة الخروج حتى العودة، واحجز مكانك في المواعيد المتاحة.', 'وصف الغلاف الرئيسي' ),
		'hu_hero_btn'   => array( 'sanitize_text_field', 'استكشف رحلات السنة', 'زر الغلاف الرئيسي' ),
		'hu_trips_title'=> array( 'sanitize_text_field', 'رحلات السنة', 'عنوان قسم الرحلات' ),
		'hu_trips_sub'  => array( 'sanitize_textarea_field', 'جميع رحلات الحج والعمرة مرتبة حسب موعد الانطلاق، اضغط على أي رحلة لعرض برنامج السير بالتفصيل من الخروج حتى العودة.', 'وصف قسم الرحلات' ),
		'hu_why_title'  => array( 'sanitize_text_field', 'لماذا تختارنا؟', 'عنوان قسم "لماذا تختارنا"' ),
		'hu_cta_title'  => array( 'sanitize_text_field', 'جاهز تبدأ رحلتك المباركة؟', 'عنوان قسم "جاهز تبدأ"' ),
		'hu_cta_sub'    => array( 'sanitize_textarea_field', 'تواصل معنا الآن واحجز مكانك في أقرب رحلة.', 'وصف قسم "جاهز تبدأ"' ),
	);
}

function hu_site_preview_cb() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}

	$saved = '';
	if ( isset( $_POST['hu_preview_save'] ) && check_admin_referer( 'hu_preview', 'hu_preview_nonce' ) ) {
		foreach ( hu_preview_text_fields() as $key => $cfg ) {
			if ( isset( $_POST[ $key ] ) ) {
				update_option( $key, call_user_func( $cfg[0], wp_unslash( $_POST[ $key ] ) ) );
			}
		}

		$order = array();
		foreach ( (array) ( $_POST['hu_section_order'] ?? array() ) as $slug ) {
			$slug = sanitize_key( $slug );
			if ( in_array( $slug, array( 'hero', 'trips', 'why', 'cta' ), true ) ) {
				$order[] = $slug;
			}
		}
		if ( $order ) {
			update_option( 'hu_home_sections', $order );
		}

		$saved = '<div class="notice notice-success" style="margin:12px 0 0;"><p>✅ تم حفظ التغييرات — انقر "تحديث المعاينة" لمشاهدة النتيجة.</p></div>';
	}

	$fields    = hu_preview_text_fields();
	$sections  = array(
		'hero'  => 'الغلاف الرئيسي (Hero)',
		'trips' => 'قسم الرحلات',
		'why'   => 'لماذا تختارنا',
		'cta'   => 'جاهز تبدأ رحلتك',
	);
	$order_cur = hu_home_sections();
	$pages     = array( 'الرئيسية' => home_url( '/' ) );
	$about     = get_page_by_path( 'about' );
	$booking   = get_page_by_path( 'booking' );
	?>
	<div class="wrap hu-preview-page">
		<h1>🖥️ معاينة الموقع وتعديله</h1>
		<p style="color:#6b7280;max-width:1200px;">شوف موقعك كاملاً كأنه زيارة عادية، وعدّل على طول من اللوحة: النصوص والترتيب في البنر، وتعديل أي صفحة أو رحلة بضغطة واحدة. أي تعديل بيظهر فوراً بعد "تحديث المعاينة".</p>

		<?php echo $saved; // phpcs:ignore ?>

		<div class="hu-preview-layout">
			<div class="hu-preview-main">
				<div class="hu-preview-toolbar">
					<select id="hu-preview-jump" title="اذهب إلى صفحة">
						<option value="<?php echo esc_url( home_url( '/?hu_preview=1' ) ); ?>">— الرئيسية —</option>
						<option value="<?php echo esc_url( get_post_type_archive_link( 'trip' ) . '?hu_preview=1' ); ?>">كل الرحلات</option>
						<?php if ( $about ) : ?>
							<option value="<?php echo esc_url( get_permalink( $about ) . '?hu_preview=1' ); ?>">من نحن</option>
						<?php endif; ?>
						<?php if ( $booking ) : ?>
							<option value="<?php echo esc_url( get_permalink( $booking ) . '?hu_preview=1' ); ?>">تواصل / حجز</option>
						<?php endif; ?>
						<?php
						$tq = hu_get_upcoming_trips();
						while ( $tq->have_posts() ) : $tq->the_post();
							?>
							<option value="<?php echo esc_url( get_permalink() . '?hu_preview=1' ); ?>">🚌 <?php echo esc_html( get_the_title() ); ?></option>
							<?php
						endwhile;
						wp_reset_postdata();
						?>
					</select>
					<button type="button" class="button" id="hu-preview-reload">↻ تحديث المعاينة</button>
					<a class="button" id="hu-preview-tab" href="<?php echo esc_url( home_url( '/' ) ); ?>" target="_blank">فتح في تبويب جديد ↗</a>
				</div>
				<iframe id="hu-preview-frame" src="<?php echo esc_url( home_url( '/?hu_preview=1' ) ); ?>" title="معاينة الموقع"></iframe>
			</div>

			<aside class="hu-preview-panel">
				<form method="post" action="">
					<?php wp_nonce_field( 'hu_preview', 'hu_preview_nonce' ); ?>

					<h3>📝 نصوص الموقع</h3>
					<table class="form-table">
						<?php foreach ( $fields as $key => $cfg ) : ?>
							<tr>
								<th><label for="<?php echo esc_attr( $key ); ?>"><?php echo esc_html( $cfg[2] ); ?></label></th>
								<td>
									<?php if ( false !== strpos( $cfg[0], 'textarea' ) ) : ?>
										<textarea id="<?php echo esc_attr( $key ); ?>" name="<?php echo esc_attr( $key ); ?>" rows="2"><?php echo esc_textarea( get_option( $key, $cfg[1] ) ); ?></textarea>
									<?php else : ?>
										<input type="text" id="<?php echo esc_attr( $key ); ?>" name="<?php echo esc_attr( $key ); ?>" value="<?php echo esc_attr( get_option( $key, $cfg[1] ) ); ?>">
									<?php endif; ?>
								</td>
							</tr>
						<?php endforeach; ?>
					</table>

					<h3>🧩 ترتيب أقسام الصفحة الرئيسية</h3>
					<p class="description" style="margin-top:0;">اكتب رقم الترتيب (1 = الأول) لكل قسم، ثم احفظ.</p>
					<?php foreach ( $sections as $slug => $label ) : ?>
						<p style="margin:6px 0;">
							<label style="display:inline-flex;align-items:center;gap:6px;">
								<input type="number" name="hu_section_order[]" value="<?php echo esc_attr( (int) array_search( $slug, $order_cur, true ) + 1 ); ?>" min="1" max="4" style="width:60px;">
								<?php echo esc_html( $label ); ?>
							</label>
						</p>
					<?php endforeach; ?>

					<h3>🖊️ تعديل مباشر</h3>
					<ul class="hu-preview-links">
						<li>الرئيسية:
							<a href="<?php echo esc_url( get_edit_post_link( 5, '' ) ); ?>" target="_blank">تعديل الصفحة</a>
						</li>
						<?php if ( $about ) : ?>
							<li>من نحن:
								<a href="<?php echo esc_url( get_edit_post_link( $about->ID, '' ) ); ?>" target="_blank">تعديل الصفحة</a>
								| <a href="<?php echo esc_url( get_permalink( $about ) ); ?>" target="_blank">عرض</a>
							</li>
						<?php endif; ?>
						<?php if ( $booking ) : ?>
							<li>تواصل / حجز:
								<a href="<?php echo esc_url( get_edit_post_link( $booking->ID, '' ) ); ?>" target="_blank">تعديل الصفحة</a>
								| <a href="<?php echo esc_url( get_permalink( $booking ) ); ?>" target="_blank">عرض</a>
							</li>
						<?php endif; ?>
						<li>رحلاتنا (الأرشيف):
							<a href="<?php echo esc_url( admin_url( 'edit.php?post_type=trip' ) ); ?>" target="_blank">كل الرحلات</a>
							| <a href="<?php echo esc_url( admin_url( 'admin.php?page=hu-add-trip' ) ); ?>">إضافة سريعة</a>
						</li>
					</ul>

					<h3>🚌 الرحلات (تعديل / معاينة)</h3>
					<ul class="hu-preview-trips">
						<?php
						$preview_q = hu_get_upcoming_trips();
						if ( $preview_q->have_posts() ) :
							while ( $preview_q->have_posts() ) : $preview_q->the_post();
								$t_dep = get_post_meta( get_the_ID(), '_hu_departure', true );
								?>
								<li>
									<button type="button" class="button-link hu-preview-go" data-url="<?php echo esc_url( get_permalink() . '?hu_preview=1' ); ?>">👁 <?php echo esc_html( get_the_title() ); ?></button>
									<div class="description">خروج: <?php echo esc_html( $t_dep ); ?> —
										<a href="<?php echo esc_url( get_edit_post_link( get_the_ID(), '' ) ); ?>" target="_blank">تعديل</a>
									</div>
								</li>
								<?php
							endwhile;
							wp_reset_postdata();
						else :
							?>
							<li>لا توجد رحلات بعد.</li>
						<?php endif; ?>
					</ul>

					<?php submit_button( '💾 حفظ كل التغييرات', 'primary large', 'hu_preview_save' ); ?>
				</form>
			</aside>
		</div>
	</div>

	<style>
	.hu-preview-layout{display:flex;gap:16px;align-items:flex-start;margin-top:14px;}
	.hu-preview-main{flex:1;min-width:0;}
	.hu-preview-panel{width:360px;max-width:100%;background:#fff;border:1px solid #dcdcde;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(0,0,0,.04);}
	.hu-preview-panel h3{margin:22px 0 8px;padding-top:14px;border-top:1px solid #f0f0f1;}
	.hu-preview-panel h3:first-child{margin-top:0;border-top:0;padding-top:0;}
	.hu-preview-panel .form-table{margin:0;}
	.hu-preview-panel .form-table th{width:120px;padding:6px 0;font-weight:600;}
	.hu-preview-panel .form-table td{padding:6px 0;}
	.hu-preview-panel .form-table input,.hu-preview-panel .form-table textarea{width:100%;}
	.hu-preview-toolbar{display:flex;gap:8px;align-items:center;background:#fff;border:1px solid #dcdcde;padding:8px 12px;border-radius:10px;margin-bottom:10px;flex-wrap:wrap;}
	#hu-preview-frame{width:100%;height:calc(100vh - 260px);min-height:500px;border:1px solid #dcdcde;border-radius:10px;background:#fff;}
	.hu-preview-links li,.hu-preview-trips li{margin:4px 0;line-height:1.6;}
	.hu-preview-trips .description{margin:0 0 6px 0;}
	.button-link{background:none;border:none;color:#2271b1;cursor:pointer;padding:0;font-size:13px;text-decoration:underline;}
	.button-link:hover{color:#135e96;}
	@media (max-width:900px){
		.hu-preview-layout{flex-direction:column;}
		.hu-preview-panel{width:100%;}
		#hu-preview-frame{height:60vh;}
	}
	</style>
	<script>
	(function () {
		var frame = document.getElementById('hu-preview-frame');
		var jump = document.getElementById('hu-preview-jump');
		var reload = document.getElementById('hu-preview-reload');
		var code = 'hu_preview=1';

		function withPrev(u) {
			try {
				var x = new URL(u, location.href);
				x.searchParams.set('hu_preview', '1');
				return x.href;
			} catch (e) {
				return u + (u.indexOf('?') === -1 ? '?' : '&') + code;
			}
		}
		if (jump) {
			jump.addEventListener('change', function () {
				frame.src = withPrev(jump.value);
			});
		}
		if (reload) {
			reload.addEventListener('click', function () {
				frame.src = withPrev(frame.getAttribute('src') || frame.src);
			});
		}
		document.querySelectorAll('.hu-preview-go').forEach(function (btn) {
			btn.addEventListener('click', function () {
				frame.src = withPrev(btn.getAttribute('data-url'));
				var sel = jump.querySelector('option[value="' + btn.getAttribute('data-url') + '"]');
				if (sel) { jump.value = sel.value; }
			});
		});
		var tab = document.getElementById('hu-preview-tab');
		if (tab) {
			tab.addEventListener('click', function () {
				tab.href = withPrev(frame.src);
			});
		}
	})();
	</script>
	<?php
}