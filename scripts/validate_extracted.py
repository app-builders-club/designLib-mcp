import json, os, re, sys

VALID_PAGE_TYPES = {"marketing_landing","about","blog_index","blog_post","careers","ecommerce_home","portfolio","pricing","product_listing","product_page","signup"}
VALID_SIGS = {"oversized_tight_tracking","editorial_spaced_paragraph_breaks","warm_desaturated_palette","rounded_card_corners","soft_card_shadows","pill_cta_buttons","tag_eyebrow_labels","sectioned_color_bands","no_gradients_on_surfaces","retro_editorial_photography","vintage_illustrated_characters","sticky_top_nav_thin","glassmorphism","neobrutalist_hard_shadow","gradient_text_hero","monochrome_photography","full_bleed_hero_imagery","split_diagonal_sections","inline_form_single_field","marquee_logo_strip","huge_wordmark_footer","data_heavy_table_grid","case_study_long_scroll","serif_display_hero","mono_accent_typography"}
VALID_MOODS = {"moody","playful","minimal","maximalist","editorial","techy","warm","cool","futuristic","retro_vintage","elegant_luxury","brutalist","organic","clinical","confident","approachable","mysterious","energetic","calm"}
VALID_PRODUCT_TYPES = {"b2b_saas","consumer_app","ai_tool","fintech_app","developer_tool","data_platform","ecommerce_fashion","ecommerce_beauty","ecommerce_home_goods","ecommerce_food_beverage","editorial_publication","media_company","creative_agency","design_studio","personal_portfolio","startup_generic","enterprise_generic","healthcare","education","nonprofit","government","marketplace","booking_service","subscription_service","hardware_product"}
VALID_STAGES = {"hero_section","whole_page","nav_only","cta_band","footer_only","feature_blocks","typography_system","color_system","photography_direction","micro_interactions","empty_states","form_design","data_display","list_view"}
SIZE_ADJ = re.compile(r"\b(oversized|huge|tiny|small|medium|large|big|gigantic|massive)\b", re.IGNORECASE)
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")

VALID_SECTIONS = set("""nav_top_split nav_top_centered nav_sidebar nav_minimal_logo_only footer_compact footer_sitemap_multi_column footer_wordmark_large breadcrumb_bar announcement_bar cookie_banner_minimal
hero_centered_above_image hero_split_left_copy_right_image hero_fullbleed_video hero_split_right_copy_left_image hero_gradient_text_only hero_stacked_cta hero_editorial_image_overlay hero_minimal_type_only hero_with_background_illustration
feature_triad_icon_row feature_card_split_image_left_copy_right feature_card_split_copy_left_image_right feature_grid_3col_image_cards feature_grid_2col_compact feature_list_two_pane_left_heading_right_stack feature_bento feature_accordion_centered feature_tabs_horizontal
social_proof_logos social_proof_metrics_row social_proof_quote_carousel testimonial_carousel testimonial_grid testimonial_single_hero press_mentions_strip
pricing_three_tier pricing_toggle_monthly_annual pricing_single_focused pricing_comparison_table pricing_calculator pricing_faq
blog_index_grid_3col blog_index_list_compact blog_index_featured_plus_grid blog_category_chips blog_search_header article_hero article_meta_bar article_body_longform article_toc_sticky_left article_pullquote article_inline_image article_author_bio_card article_related_posts_grid article_share_bar article_next_prev_nav
about_mission_statement about_team_grid about_team_list about_timeline about_values_grid about_founding_story about_office_photos about_press_coverage
careers_mission careers_open_roles_list careers_open_roles_filters careers_benefits_grid careers_culture_images careers_team_interviews careers_process_steps
portfolio_work_grid portfolio_work_list_scroll portfolio_case_study_hero portfolio_case_study_body portfolio_services_list portfolio_clients_logos portfolio_contact_cta
ecom_hero_editorial ecom_featured_collections_grid ecom_new_arrivals_carousel ecom_category_tiles ecom_lookbook_band ecom_ugc_gallery ecom_story_band
plist_category_hero plist_filter_sidebar_grid plist_filter_top_bar_grid plist_sort_toolbar plist_grid_2col plist_grid_3col plist_grid_4col plist_pagination plist_infinite_scroll
pdp_gallery_sticky_left_info_right pdp_gallery_top_info_below pdp_gallery_fullbleed_info_overlay pdp_variants_picker pdp_size_picker pdp_add_to_cart_sticky pdp_details_accordion pdp_shipping_returns_strip pdp_reviews_summary pdp_reviews_list pdp_recommended_products pdp_editorial_story_band
signup_form_centered signup_split_form_illustration signup_split_form_photo signup_oauth_only signup_multistep signup_testimonial_sidebar signup_pricing_preview
quote_band_search_mock quote_band_oversized_pullquote resources_grid_3col resources_list_compact final_cta_illustrated final_cta_plain final_cta_email_capture faq_accordion stats_band contact_split_form_map""".split())

def find_section_strings(node, path=""):
    if isinstance(node, dict):
        for k,v in node.items():
            yield from find_section_strings(v, path + "." + k)
    elif isinstance(node, list):
        for i,v in enumerate(node):
            yield from find_section_strings(v, path + "[" + str(i) + "]")
    elif isinstance(node, str):
        yield (path, node)

def scan_for_size_adj(node, path=""):
    out=[]
    if isinstance(node, dict):
        for k,v in node.items():
            if k == "size_token": continue
            out += scan_for_size_adj(v, path + "." + k)
    elif isinstance(node, list):
        for i,v in enumerate(node):
            out += scan_for_size_adj(v, path + "[" + str(i) + "]")
    elif isinstance(node, str):
        m = SIZE_ADJ.search(node)
        if m:
            out.append("size adj '" + m.group(0) + "' at " + path + ": " + repr(node[:80]))
    return out

files = sys.argv[1:]
total_fail = 0
for fp in files:
    issues=[]
    try:
        with open(fp, encoding='utf-8') as fh:
            d = json.load(fh)
    except Exception as e:
        print("PARSE-FAIL " + fp + ": " + str(e)); total_fail += 1; continue

    pt = d.get("classification",{}).get("page_type")
    if pt not in VALID_PAGE_TYPES: issues.append("page_type " + repr(pt) + " not in vocab")
    lpid = d.get("classification",{}).get("landing_pattern_id")
    if pt == "marketing_landing":
        if not lpid: issues.append("landing_pattern_id null on marketing_landing")
    else:
        if lpid: issues.append("landing_pattern_id set on non-landing (" + str(pt) + ")")

    so = d.get("section_order") or []
    secs = d.get("sections") or []
    if len(so) != len(secs): issues.append("section_order/sections length mismatch (" + str(len(so)) + " vs " + str(len(secs)) + ")")
    for i,(a,b) in enumerate(zip(so, [s.get("type") for s in secs])):
        if a != b: issues.append("section_order[" + str(i) + "]=" + repr(a) + " vs sections[" + str(i) + "].type=" + repr(b))
    for s in secs:
        if s.get("type") not in VALID_SECTIONS:
            issues.append("unknown section type: " + repr(s.get("type")))

    for sig in d.get("visual_signatures") or []:
        if sig not in VALID_SIGS: issues.append("unknown visual_signature: " + repr(sig))

    moods = d.get("classification",{}).get("mood") or []
    if not (2 <= len(moods) <= 6): issues.append("classification.mood count " + str(len(moods)) + " not in 2..6")
    for m in moods:
        if m not in VALID_MOODS: issues.append("unknown mood: " + repr(m))

    im = d.get("inspiration_metadata",{})
    gpt = im.get("good_for_product_types") or []
    if not (2 <= len(gpt) <= 6): issues.append("good_for_product_types count " + str(len(gpt)) + " not in 2..6")
    for x in gpt:
        if x not in VALID_PRODUCT_TYPES: issues.append("unknown product_type: " + repr(x))
    gm = im.get("good_for_moods") or []
    if not (2 <= len(gm) <= 6): issues.append("good_for_moods count " + str(len(gm)) + " not in 2..6")
    for x in gm:
        if x not in VALID_MOODS: issues.append("unknown im.mood: " + repr(x))
    gs = im.get("good_for_stages") or []
    if not (1 <= len(gs) <= 5): issues.append("good_for_stages count " + str(len(gs)) + " not in 1..5")
    for x in gs:
        if x not in VALID_STAGES: issues.append("unknown stage: " + repr(x))

    kws = d.get("keywords") or []
    if not (8 <= len(kws) <= 20): issues.append("keywords count " + str(len(kws)) + " not in 8..20")

    # generation_constraints stays tightly tied to landing/signup (it encodes
    # full-page hard_rules/soft_guidance; only meaningful where there is a
    # landing_pattern_id to anchor on).
    # generation_prompt is required for landing/signup but allowed for any
    # page_type since migration 007 — non-landing pages may carry a 2-4
    # sentence "spirit-of-the-page" seed.
    gp = d.get("generation_prompt"); gc = d.get("generation_constraints")
    if pt in ("marketing_landing","signup"):
        if not gp: issues.append("generation_prompt null on landing/signup")
        if not gc: issues.append("generation_constraints null on landing/signup")
    else:
        if gc is not None: issues.append("generation_constraints non-null on non-landing/signup")
    if gp is not None and not isinstance(gp, str):
        issues.append("generation_prompt is not a string")

    uw = d.get("use_when")
    if uw is not None and not isinstance(uw, str):
        issues.append("use_when is not a string")

    role_intent = d.get("palette",{}).get("role_intent",{}) or {}
    if not isinstance(role_intent, dict):
        issues.append("palette.role_intent is not an object (got " + type(role_intent).__name__ + ")")
        role_intent = {}
    for k,v in role_intent.items():
        if isinstance(v,str) and v.upper() in ("#FFFFFF","#000000"):
            issues.append("pure " + v + " in role_intent." + k)

    for path, val in find_section_strings(d.get("sections",[])):
        if HEX.search(val):
            issues.append("hex inside sections at " + path + ": " + repr(val))

    issues += scan_for_size_adj(d)

    if issues:
        total_fail += 1
        print("\nFAIL " + fp)
        for i in issues: print("  - " + i)
    else:
        print("OK   " + fp)

print("\n=== summary: " + str(len(files)-total_fail) + " ok, " + str(total_fail) + " fail ===")
