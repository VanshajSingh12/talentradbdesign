-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Notifications, preferences and community module
-- Phase 4 (Individual/Team, Member C / Team), Milestones 15-18
--
-- This file models ONLY the docket Notifications, preferences and community domain.
-- Tier 1 (mandatory) from Section 4:
--   notifications and alert preferences
-- Tier 2 (modelled because you chose to model all Tier 2):
--   notification preferences, job alert preferences, language preference,
--     privacy settings, notification deliveries, community posts and reactions,
--     support tickets, FAQs, referral events.
--
-- B57 deliverable: high-volume write path for deliveries. The notification delivery
--   table is designed for high-volume inserts (append-only, minimal indexes for the
--   hot path, partitioned-friendly shape where applicable). The exact partitioning
--   strategy is documented in 99_documentation.sql.
--
-- Naming follows Rule Group 1 exactly. PK = id. FK = <referenced>_id.
-- Rule Group 2: BIGINT surrogate PK; natural keys as unique constraints.
-- Rule Group 3: standard domains applied and cited inline.
-- Rule Group 4: created_at, created_by, updated_at, updated_by on business tables;
--   soft-delete where stated; audit append-only elsewhere.
-- Rule Group 5: nullable columns justified; unknown vs not applicable distinction kept.
-- Rule Group 6: sensitive classification where applicable.
-- Rule Group 7: multilingual stored with language where known; UI keys via ui_translation.
-- Rule Group 8: analytics objects prefixed analytics_ (in analytics module, not here).
-- Rule Group 9 / 10: not Notifications module concerns for those specifics.
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- NOTIFICATION PREFERENCE
-- Tier 1/2: notification preferences.
-- Relationship:
--   users 1..* notification_preference
-- -----------------------------------------------------------------------------
CREATE TABLE notification_preference (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    channel_code           TEXT      NOT NULL,
    notification_type_code TEXT      NOT NULL,
    is_enabled             BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_notification_preference_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_notification_preference_user_channel_type UNIQUE (user_id, channel_code, notification_type_code)
);

CREATE INDEX idx_notification_preference_user ON notification_preference (user_id);
CREATE INDEX idx_notification_preference_channel ON notification_preference (channel_code);
CREATE INDEX idx_notification_preference_type ON notification_preference (notification_type_code);
CREATE INDEX idx_notification_preference_enabled ON notification_preference (user_id, channel_code, notification_type_code, is_enabled)
    WHERE is_enabled = TRUE;
CREATE INDEX idx_notification_preference_deleted ON notification_preference (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE notification_preference IS 'Notifications, preferences and community: notification preferences (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN notification_preference.channel_code IS 'Enumeration code referencing reference_code (domain=notification_channel).';

COMMENT ON COLUMN notification_preference.notification_type_code IS 'Enumeration code referencing reference_code (domain=notification_type).';

COMMENT ON COLUMN notification_preference.is_enabled IS 'Boolean flag with stated default TRUE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- JOB ALERT PREFERENCE
-- Tier 1/2: job alert preferences.
-- Relationship:
--   users 1..* job_alert_preference
-- Job alert preferences carry the alert criteria as text/json and the delivery channels.
-- -----------------------------------------------------------------------------
CREATE TABLE job_alert_preference (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    alert_name             TEXT      NOT NULL,
    criteria               TEXT      NOT NULL,
    frequency_code          TEXT      NOT NULL,
    delivery_channel_codes TEXT      NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_job_alert_preference_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_job_alert_preference_user_name UNIQUE (user_id, alert_name)
);

CREATE INDEX idx_job_alert_preference_user ON job_alert_preference (user_id);
CREATE INDEX idx_job_alert_preference_frequency ON job_alert_preference (frequency_code);
CREATE INDEX idx_job_alert_preference_active ON job_alert_preference (user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_job_alert_preference_deleted ON job_alert_preference (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE job_alert_preference IS 'Notifications, preferences and community: job alert preferences (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN job_alert_preference.alert_name IS 'Alert name; unique per user.';

COMMENT ON COLUMN job_alert_preference.criteria IS 'Free text domain TEXT; job alert criteria (search criteria representation). Bounded length enforced at application level.';

COMMENT ON COLUMN job_alert_preference.frequency_code IS 'Enumeration code referencing reference_code (domain=alert_frequency).';

COMMENT ON COLUMN job_alert_preference.delivery_channel_codes IS 'Nullable = no channels. Comma-separated or JSON list of channel codes for delivery.';

COMMENT ON COLUMN job_alert_preference.is_active IS 'Boolean flag with stated default TRUE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- LANGUAGE PREFERENCE
-- Tier 1/2: language preference.
-- Relationship:
--   users 1..1 language_preference (one per user)
-- -----------------------------------------------------------------------------
CREATE TABLE language_preference (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    ui_language_code       TEXT      NULL,
    content_language_code  TEXT      NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_language_preference_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_language_preference_user UNIQUE (user_id)
);

CREATE INDEX idx_language_preference_user ON language_preference (user_id);
CREATE INDEX idx_language_preference_ui_language ON language_preference (ui_language_code) WHERE ui_language_code IS NOT NULL;
CREATE INDEX idx_language_preference_content_language ON language_preference (content_language_code) WHERE content_language_code IS NOT NULL;
CREATE INDEX idx_language_preference_deleted ON language_preference (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE language_preference IS 'Notifications, preferences and community: language preference (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN language_preference.ui_language_code IS 'Nullable = not set. Language code for UI; stored as text code.';

COMMENT ON COLUMN language_preference.content_language_code IS 'Nullable = not set. Language code for content preferences.';

COMMENT ON COLUMN language_preference.is_active IS 'Boolean flag with stated default TRUE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- PRIVACY SETTING
-- Tier 1/2: privacy settings.
-- Relationship:
--   users 1..* privacy_setting
-- -----------------------------------------------------------------------------
CREATE TABLE privacy_setting (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                BIGINT    NOT NULL,
    setting_key            TEXT      NOT NULL,
    setting_value          TEXT      NOT NULL,
    setting_type_code      TEXT      NULL,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_privacy_setting_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_privacy_setting_user_key UNIQUE (user_id, setting_key)
);

CREATE INDEX idx_privacy_setting_user ON privacy_setting (user_id);
CREATE INDEX idx_privacy_setting_key ON privacy_setting (setting_key);
CREATE INDEX idx_privacy_setting_active ON privacy_setting (user_id, setting_key, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_privacy_setting_deleted ON privacy_setting (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE privacy_setting IS 'Notifications, preferences and community: privacy settings (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN privacy_setting.setting_key IS 'Privacy setting key; unique per user.';

COMMENT ON COLUMN privacy_setting.setting_value IS 'Privacy setting value; stored as text.';

COMMENT ON COLUMN privacy_setting.setting_type_code IS 'Nullable = type not set. Enumeration code referencing reference_code (domain=setting_type).';

COMMENT ON COLUMN privacy_setting.is_active IS 'Boolean flag with stated default TRUE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- NOTIFICATION DELIVERY
-- Tier 1/2: notification deliveries.
-- B57 deliverable: high-volume write path for deliveries.
-- This table is append-only for the delivery hot path. Indexes are kept minimal on the
--   hot path; additional read indexes are added only where required. The partitioning
--   strategy is documented in 99_documentation.sql.
-- Relationship:
--   users (recipient) 1..* notification_delivery
-- -----------------------------------------------------------------------------
CREATE TABLE notification_delivery (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recipient_user_id      BIGINT    NOT NULL,
    notification_type_code TEXT      NOT NULL,
    channel_code           TEXT      NOT NULL,
    subject                TEXT      NOT NULL,
    body_text              TEXT      NULL,
    delivery_status_code   TEXT      NOT NULL,
    scheduled_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at                TIMESTAMPTZ NULL,
    delivered_at           TIMESTAMPTZ NULL,
    read_at                TIMESTAMPTZ NULL,
    delivery_reference     TEXT      NULL,
    delivery_error         TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_notification_delivery_recipient FOREIGN KEY (recipient_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_notification_delivery_scheduled CHECK (scheduled_at <= now())
);

CREATE INDEX idx_notification_delivery_recipient ON notification_delivery (recipient_user_id);
CREATE INDEX idx_notification_delivery_status ON notification_delivery (delivery_status_code);
CREATE INDEX idx_notification_delivery_scheduled_at ON notification_delivery (scheduled_at);
CREATE INDEX idx_notification_delivery_sent_at ON notification_delivery (sent_at) WHERE sent_at IS NOT NULL;
CREATE INDEX idx_notification_delivery_delivered_at ON notification_delivery (delivered_at) WHERE delivered_at IS NOT NULL;
CREATE INDEX idx_notification_delivery_read_at ON notification_delivery (read_at) WHERE read_at IS NOT NULL;

COMMENT ON TABLE notification_delivery IS 'Notifications, preferences and community: notification deliveries (Section 4 Tier 1/2). Personal. High-volume write path (B57).';

COMMENT ON COLUMN notification_delivery.notification_type_code IS 'Enumeration code referencing reference_code (domain=notification_type).';

COMMENT ON COLUMN notification_delivery.channel_code IS 'Enumeration code referencing reference_code (domain=notification_channel).';

COMMENT ON COLUMN notification_delivery.subject IS 'Notification subject; free text domain TEXT; bounded length enforced at application level.';

COMMENT ON COLUMN notification_delivery.body_text IS 'Nullable = no body. Notification body stored only as needed for audit (Section 6 messaging boundary: does not store message bodies longer than required for audit).';

COMMENT ON COLUMN notification_delivery.delivery_status_code IS 'Enumeration code referencing reference_code (domain=delivery_status).';

COMMENT ON COLUMN notification_delivery.scheduled_at IS 'Scheduled delivery time.';

COMMENT ON COLUMN notification_delivery.sent_at IS 'Nullable = not sent yet.';

COMMENT ON COLUMN notification_delivery.delivered_at IS 'Nullable = not delivered yet.';

COMMENT ON COLUMN notification_delivery.read_at IS 'Nullable = not read.';

COMMENT ON COLUMN notification_delivery.delivery_reference IS 'Nullable = no reference. Reference to the messaging provider delivery, not message body (Section 6 messaging boundary).';

COMMENT ON COLUMN notification_delivery.delivery_error IS 'Nullable = no error.';

-- -----------------------------------------------------------------------------
-- COMMUNITY POST
-- Tier 1/2: community posts.
-- Relationship:
--   users (author) 1..* community_post
-- -----------------------------------------------------------------------------
CREATE TABLE community_post (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_user_id         BIGINT    NOT NULL,
    community_type_code    TEXT      NOT NULL,
    title                  TEXT      NULL,
    body_text              TEXT      NOT NULL,
    language_code          TEXT      NULL,
    visibility_code        TEXT      NOT NULL,
    is_pinned              BOOLEAN   NOT NULL DEFAULT FALSE,
    is_published           BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_community_post_author FOREIGN KEY (author_user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_community_post_body CHECK (char_length(body_text) > 0)
);

CREATE INDEX idx_community_post_author ON community_post (author_user_id);
CREATE INDEX idx_community_post_type ON community_post (community_type_code);
CREATE INDEX idx_community_post_visibility ON community_post (visibility_code);
CREATE INDEX idx_community_post_published ON community_post (is_published) WHERE is_published = TRUE;
CREATE INDEX idx_community_post_created_at ON community_post (created_at);
CREATE INDEX idx_community_post_deleted ON community_post (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE community_post IS 'Notifications, preferences and community: community posts (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN community_post.community_type_code IS 'Enumeration code referencing reference_code (domain=community_type).';

COMMENT ON COLUMN community_post.title IS 'Nullable = no title.';

COMMENT ON COLUMN community_post.body_text IS 'Free text domain TEXT; community post body. Bounded length enforced at application level.';

COMMENT ON COLUMN community_post.language_code IS 'Nullable = unknown language. Language recorded where known (Rule Group 7).';

COMMENT ON COLUMN community_post.visibility_code IS 'Enumeration code referencing reference_code (domain=post_visibility).';

COMMENT ON COLUMN community_post.is_pinned IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

COMMENT ON COLUMN community_post.is_published IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- COMMUNITY POST REACTION
-- Tier 1/2: community post reactions.
-- Relationship:
--   community_post 1..* community_post_reaction
--   users (reactor) 1..* community_post_reaction
-- -----------------------------------------------------------------------------
CREATE TABLE community_post_reaction (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    community_post_id      BIGINT    NOT NULL,
    reactor_user_id        BIGINT    NOT NULL,
    reaction_type_code     TEXT      NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_community_post_reaction_post FOREIGN KEY (community_post_id)
        REFERENCES community_post(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_community_post_reaction_reactor FOREIGN KEY (reactor_user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_community_post_reaction_post_reactor UNIQUE (community_post_id, reactor_user_id)
);

CREATE INDEX idx_community_post_reaction_post ON community_post_reaction (community_post_id);
CREATE INDEX idx_community_post_reaction_reactor ON community_post_reaction (reactor_user_id);
CREATE INDEX idx_community_post_reaction_type ON community_post_reaction (reaction_type_code);
CREATE INDEX idx_community_post_reaction_deleted ON community_post_reaction (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE community_post_reaction IS 'Notifications, preferences and community: community post reactions (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN community_post_reaction.reaction_type_code IS 'Enumeration code referencing reference_code (domain=reaction_type).';

-- -----------------------------------------------------------------------------
-- SUPPORT TICKET
-- Tier 1/2: support tickets.
-- Relationship:
--   users (reporter) 1..* support_ticket
--   users (assignee) 1..* support_ticket
-- -----------------------------------------------------------------------------
CREATE TABLE support_ticket (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reporter_user_id       BIGINT    NOT NULL,
    assignee_user_id       BIGINT    NULL,
    category_code          TEXT      NOT NULL,
    priority_code          TEXT      NOT NULL,
    status_code            TEXT      NOT NULL,
    subject                TEXT      NOT NULL,
    description            TEXT      NULL,
    language_code          TEXT      NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_support_ticket_reporter FOREIGN KEY (reporter_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_support_ticket_assignee FOREIGN KEY (assignee_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_support_ticket_subject CHECK (char_length(subject) > 0)
);

CREATE INDEX idx_support_ticket_reporter ON support_ticket (reporter_user_id);
CREATE INDEX idx_support_ticket_assignee ON support_ticket (assignee_user_id) WHERE assignee_user_id IS NOT NULL;
CREATE INDEX idx_support_ticket_category ON support_ticket (category_code);
CREATE INDEX idx_support_ticket_priority ON support_ticket (priority_code);
CREATE INDEX idx_support_ticket_status ON support_ticket (status_code);
CREATE INDEX idx_support_ticket_created_at ON support_ticket (created_at);
CREATE INDEX idx_support_ticket_deleted ON support_ticket (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE support_ticket IS 'Notifications, preferences and community: support tickets (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN support_ticket.category_code IS 'Enumeration code referencing reference_code (domain=support_category).';

COMMENT ON COLUMN support_ticket.priority_code IS 'Enumeration code referencing reference_code (domain=support_priority).';

COMMENT ON COLUMN support_ticket.status_code IS 'Enumeration code referencing reference_code (domain=support_status).';

COMMENT ON COLUMN support_ticket.subject IS 'Support ticket subject.';

COMMENT ON COLUMN support_ticket.description IS 'Nullable = no description. Free text domain TEXT; bounded length enforced at application level.';

COMMENT ON COLUMN support_ticket.language_code IS 'Nullable = unknown language. Language recorded where known (Rule Group 7).';

-- -----------------------------------------------------------------------------
-- SUPPORT TICKET REPLY
-- Tier 1/2: support ticket replies.
-- Relationship:
--   support_ticket 1..* support_ticket_reply
--   users (reply author) 1..* support_ticket_reply
-- -----------------------------------------------------------------------------
CREATE TABLE support_ticket_reply (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    support_ticket_id      BIGINT    NOT NULL,
    reply_author_user_id   BIGINT    NOT NULL,
    reply_text             TEXT      NOT NULL,
    is_internal            BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_support_ticket_reply_ticket FOREIGN KEY (support_ticket_id)
        REFERENCES support_ticket(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_support_ticket_reply_author FOREIGN KEY (reply_author_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_support_ticket_reply_text CHECK (char_length(reply_text) > 0)
);

CREATE INDEX idx_support_ticket_reply_ticket ON support_ticket_reply (support_ticket_id);
CREATE INDEX idx_support_ticket_reply_author ON support_ticket_reply (reply_author_user_id);
CREATE INDEX idx_support_ticket_reply_created_at ON support_ticket_reply (created_at);
CREATE INDEX idx_support_ticket_reply_internal ON support_ticket_reply (is_internal) WHERE is_internal = TRUE;
CREATE INDEX idx_support_ticket_reply_deleted ON support_ticket_reply (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE support_ticket_reply IS 'Notifications, preferences and community: support ticket replies (Section 4 Tier 1/2). Personal. Soft-deleted.';

COMMENT ON COLUMN support_ticket_reply.reply_text IS 'Support ticket reply text.';

COMMENT ON COLUMN support_ticket_reply.is_internal IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain). Internal replies are staff-only notes.';

-- -----------------------------------------------------------------------------
-- FAQ
-- Tier 1/2: FAQs.
-- Relationship: standalone reference data; linked to language where known.
-- -----------------------------------------------------------------------------
CREATE TABLE faq (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_code          TEXT      NOT NULL,
    question               TEXT      NOT NULL,
    answer                 TEXT      NOT NULL,
    language_code          TEXT      NULL,
    sort_order             SMALLINT  NOT NULL DEFAULT 0,
    is_published           BOOLEAN   NOT NULL DEFAULT FALSE,
    view_count             INTEGER   NOT NULL DEFAULT 0,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT chk_faq_question CHECK (char_length(question) > 0),
    CONSTRAINT chk_faq_answer CHECK (char_length(answer) > 0),
    CONSTRAINT chk_faq_view_count_nonnegative CHECK (view_count >= 0)
);

CREATE INDEX idx_faq_category ON faq (category_code);
CREATE INDEX idx_faq_language ON faq (language_code) WHERE language_code IS NOT NULL;
CREATE INDEX idx_faq_published ON faq (is_published) WHERE is_published = TRUE;
CREATE INDEX idx_faq_sort_order ON faq (category_code, sort_order);
CREATE INDEX idx_faq_view_count ON faq (view_count DESC);
CREATE INDEX idx_faq_deleted ON faq (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE faq IS 'Notifications, preferences and community: FAQs (Section 4 Tier 1/2). Internal/Public. Soft-deleted.';

COMMENT ON COLUMN faq.category_code IS 'Enumeration code referencing reference_code (domain=faq_category).';

COMMENT ON COLUMN faq.question IS 'FAQ question.';

COMMENT ON COLUMN faq.answer IS 'FAQ answer; free text domain TEXT; bounded length enforced at application level.';

COMMENT ON COLUMN faq.language_code IS 'Nullable = unknown language. Language recorded where known (Rule Group 7).';

COMMENT ON COLUMN faq.sort_order IS 'Sort order within category.';

COMMENT ON COLUMN faq.is_published IS 'Boolean flag with stated default FALSE (Rule Group 3 boolean domain).';

COMMENT ON COLUMN faq.view_count IS 'FAQ view count; nonnegative.';

-- -----------------------------------------------------------------------------
-- FAQ CATEGORY
-- Tier 1/2: FAQ categories.
-- Relationship: standalone reference data.
-- -----------------------------------------------------------------------------
CREATE TABLE faq_category (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_code          TEXT      NOT NULL,
    name                   TEXT      NOT NULL,
    description            TEXT      NULL,
    sort_order             SMALLINT  NOT NULL DEFAULT 0,
    is_active              BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT uq_faq_category_code UNIQUE (category_code)
);

CREATE INDEX idx_faq_category_code ON faq_category (category_code);
CREATE INDEX idx_faq_category_active ON faq_category (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_faq_category_deleted ON faq_category (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE faq_category IS 'Notifications, preferences and community: FAQ categories (Section 4 Tier 1/2). Internal. Soft-deleted.';

COMMENT ON COLUMN faq_category.category_code IS 'FAQ category code; unique per category.';

COMMENT ON COLUMN faq_category.name IS 'FAQ category name.';

COMMENT ON COLUMN faq_category.description IS 'Nullable = no description.';

COMMENT ON COLUMN faq_category.sort_order IS 'Sort order for categories.';

COMMENT ON COLUMN faq_category.is_active IS 'Boolean flag with stated default TRUE (Rule Group 3 boolean domain).';

-- -----------------------------------------------------------------------------
-- REFERRAL EVENT
-- Tier 1/2: referral events.
-- Relationship:
--   users (referrer) 1..* referral_event
--   users (referred) 1..* referral_event (optional)
--   candidate_identity 1..* referral_event (optional, for candidate referrals)
--   job_requirement 1..* referral_event (optional, for job referrals)
-- The docket lists referral events under Notifications, preferences and community.
-- -----------------------------------------------------------------------------
CREATE TABLE referral_event (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    referrer_user_id       BIGINT    NOT NULL,
    referred_user_id       BIGINT    NULL,
    referred_candidate_id  BIGINT    NULL,
    referred_job_id        BIGINT    NULL,
    referral_type_code     TEXT      NOT NULL,
    event_type_code        TEXT      NOT NULL,
    event_detail           TEXT      NULL,
    occurred_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT    NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT    NOT NULL DEFAULT 0,
    deleted_at             TIMESTAMPTZ NULL,
    CONSTRAINT fk_referral_event_referrer FOREIGN KEY (referrer_user_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_referral_event_referred_user FOREIGN KEY (referred_user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_referral_event_referred_candidate FOREIGN KEY (referred_candidate_id)
        REFERENCES candidate_identity(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_referral_event_referred_job FOREIGN KEY (referred_job_id)
        REFERENCES job_requirement(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX idx_referral_event_referrer ON referral_event (referrer_user_id);
CREATE INDEX idx_referral_event_referred_user ON referral_event (referred_user_id) WHERE referred_user_id IS NOT NULL;
CREATE INDEX idx_referral_event_referred_candidate ON referral_event (referred_candidate_id) WHERE referred_candidate_id IS NOT NULL;
CREATE INDEX idx_referral_event_referred_job ON referral_event (referred_job_id) WHERE referred_job_id IS NOT NULL;
CREATE INDEX idx_referral_event_type ON referral_event (referral_type_code);
CREATE INDEX idx_referral_event_event_type ON referral_event (event_type_code);
CREATE INDEX idx_referral_event_occurred_at ON referral_event (occurred_at);
CREATE INDEX idx_referral_event_deleted ON referral_event (deleted_at) WHERE deleted_at IS NOT NULL;

COMMENT ON TABLE referral_event IS 'Notifications, preferences and community: referral events (Section 4 Tier 1/2). Internal. Soft-deleted.';

COMMENT ON COLUMN referral_event.referral_type_code IS 'Enumeration code referencing reference_code (domain=referral_type).';

COMMENT ON COLUMN referral_event.event_type_code IS 'Enumeration code referencing reference_code (domain=referral_event_type).';

COMMENT ON COLUMN referral_event.event_detail IS 'Nullable = no detail. Free text domain TEXT; bounded length enforced at application level.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Notifications, preferences and community (Milestone 16, B51)
--   users 1..* notification_preference
--   users 1..* job_alert_preference
--   users 1..1 language_preference
--   users 1..* privacy_setting
--   users 1..* notification_delivery (recipient)
--   users 1..* community_post (author)
--   community_post 1..* community_post_reaction
--   users 1..* community_post_reaction (reactor)
--   users 1..* support_ticket (reporter)
--   users 1..* support_ticket (assignee)
--   support_ticket 1..* support_ticket_reply
--   users 1..* support_ticket_reply (reply author)
--   faq (standalone, linked to language where known)
--   faq_category (standalone)
--   users 1..* referral_event (referrer)
--   users 1..* referral_event (referred user)
--   candidate_identity 1..* referral_event (referred candidate)
--   job_requirement 1..* referral_event (referred job)
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new Notifications entities beyond the docket list. Decisions taken:
--   1. notification_delivery is designed for high-volume writes (B57) with minimal hot-path
--      indexes; partitioning strategy is documented in 99_documentation.sql.
--   2. body_text on notification_delivery is stored only as needed for audit, consistent
--      with the messaging boundary in Section 6 (does not store message bodies longer than
--      required for audit).
--   3. community_post and support_ticket replies are soft-deleted.
--   4. referral_event is the referral events table for the Notifications, preferences and
--      community module.
-- All recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
