from datetime import datetime, timedelta
import bcrypt

async def seed_database(db):
    """Seed database with initial data"""
    
    # Seed admin user
    admin_exists = await db.admin_users.find_one({"email": "admin@PurpleOps.com"})
    if not admin_exists:
        hashed_password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        await db.admin_users.insert_one({
            "email": "admin@PurpleOps.com",
            "password": hashed_password,
            "firstName": "Admin",
            "lastName": "User",
            "role": "admin",
            "permissions": ["all"],
            "createdAt": datetime.utcnow()
        })
        print("✓ Admin user seeded")
    
    # Seed header content
    header_exists = await db.website_content.find_one({"section": "header"})
    if not header_exists:
        await db.website_content.insert_one({
            "section": "header",
            "content": {
                "navLinks": [
                    {"name": "Home", "path": "/"},
                    {"name": "About", "path": "/about"},
                    {"name": "Blog", "path": "/blog"}
                ]
            },
            "updatedAt": datetime.utcnow()
        })
        print("✓ Header content seeded")
    
    # Seed footer content
    footer_exists = await db.website_content.find_one({"section": "footer"})
    if not footer_exists:
        await db.website_content.insert_one({
            "section": "footer",
            "content": {
                "sections": [
                    {
                        "title": "Product",
                        "links": [
                            {"name": "Features", "path": "/"},
                            {"name": "Security", "path": "/about"},
                            {"name": "Integrations", "path": "#"},
                            {"name": "Pricing", "path": "#"},
                            {"name": "API", "path": "#"}
                        ]
                    },
                    {
                        "title": "Solutions",
                        "links": [
                            {"name": "Enterprise", "path": "#"},
                            {"name": "Small Business", "path": "#"},
                            {"name": "Government", "path": "#"},
                            {"name": "Healthcare", "path": "#"},
                            {"name": "Finance", "path": "#"}
                        ]
                    },
                    {
                        "title": "Resources",
                        "links": [
                            {"name": "Blog", "path": "/blog"},
                            {"name": "Documentation", "path": "#"},
                            {"name": "Help Center", "path": "#"},
                            {"name": "Case Studies", "path": "#"},
                            {"name": "Webinars", "path": "#"}
                        ]
                    },
                    {
                        "title": "Company",
                        "links": [
                            {"name": "About Us", "path": "/about"},
                            {"name": "Careers", "path": "#"},
                            {"name": "News", "path": "#"},
                            {"name": "Contact", "path": "#"},
                            {"name": "Partners", "path": "#"}
                        ]
                    }
                ],
                "socialLinks": [
                    {"name": "LinkedIn", "url": "#", "icon": "linkedin"},
                    {"name": "Twitter", "url": "#", "icon": "twitter"},
                    {"name": "GitHub", "url": "#", "icon": "github"}
                ]
            },
            "updatedAt": datetime.utcnow()
        })
        print("✓ Footer content seeded")
    
#     # Seed website content
#     sections = ["hero", "features", "about", "services", "testimonials"]
#     for section in sections:
#         exists = await db.website_content.find_one({"section": section})
#         if not exists:
#             content = get_default_content(section)
#             await db.website_content.insert_one({
#                 "section": section,
#                 "content": content,
#                 "updatedAt": datetime.utcnow()
#             })
#     print("✓ Website content seeded")
    
#     # Seed sample blog posts
#     blog_count = await db.blog_posts.count_documents({})
#     if blog_count == 0:
#         posts = [
#             {
#                 "title": "Advanced Threat Detection with AI",
#                 "slug": "advanced-threat-detection-ai",
#                 "content": "<p>Artificial Intelligence is revolutionizing how we detect and respond to cyber threats...</p>",
#                 "excerpt": "Learn how AI is transforming cybersecurity threat detection.",
#                 "author": "PurpleOps Team",
#                 "category": "Technology",
#                 "tags": ["AI", "Threat Detection", "Security"],
#                 "status": "published",
#                 "createdAt": datetime.utcnow(),
#                 "updatedAt": datetime.utcnow()
#             },
#             {
#                 "title": "Zero Trust Architecture Guide",
#                 "slug": "zero-trust-architecture-guide",
#                 "content": "<p>Implementing zero trust security requires a fundamental shift in thinking...</p>",
#                 "excerpt": "A comprehensive guide to implementing zero trust security.",
#                 "author": "PurpleOps Team",
#                 "category": "Best Practices",
#                 "tags": ["Zero Trust", "Architecture", "Security"],
#                 "status": "published",
#                 "createdAt": datetime.utcnow(),
#                 "updatedAt": datetime.utcnow()
#             },
#             {
#                 "title": "Ransomware Prevention Strategies",
#                 "slug": "ransomware-prevention-strategies",
#                 "content": "<p>Protecting your organization from ransomware requires multiple layers of defense...</p>",
#                 "excerpt": "Essential strategies to protect against ransomware attacks.",
#                 "author": "PurpleOps Team",
#                 "category": "Prevention",
#                 "tags": ["Ransomware", "Prevention", "Security"],
#                 "status": "published",
#                 "createdAt": datetime.utcnow(),
#                 "updatedAt": datetime.utcnow()
#             }
#         ]
#         await db.blog_posts.insert_many(posts)
#         print("✓ Blog posts seeded")
    
#     # Seed security events for client dashboard
#     events_count = await db.security_events.count_documents({})
#     if events_count == 0:
#         events = generate_security_events()
#         await db.security_events.insert_many(events)
#         print("✓ Security events seeded")

# def get_default_content(section):
#     defaults = {
#         "hero": {
#             "title": "Secure Your Digital Assets with PurpleOps",
#             "subtitle": "Advanced cybersecurity analytics and threat detection platform designed for modern organizations.",
#             "ctaText": "Get Started",
#             "ctaLink": "/book-demo"
#         },
#         "features": {
#             "title": "Advanced Security Features",
#             "items": [
#                 {"title": "Real-Time Threat Detection", "description": "AI-powered threat detection that identifies attacks in milliseconds."},
#                 {"title": "Advanced Monitoring", "description": "Comprehensive visibility across your entire digital infrastructure."},
#                 {"title": "Automated Response", "description": "Instant automated responses to security threats."},
#                 {"title": "Analytics Dashboard", "description": "Rich analytics and reporting for security insights."}
#             ]
#         },
#         "about": {
#             "title": "About PurpleOps",
#             "description": "PurpleOps is a leading cybersecurity company dedicated to protecting organizations from evolving threats.",
#             "mission": "Our mission is to provide world-class security solutions that enable businesses to operate safely in the digital age."
#         },
#         "services": {
#             "title": "Our Services",
#             "items": [
#                 {"title": "Threat Detection", "description": "24/7 monitoring and threat detection services."},
#                 {"title": "Incident Response", "description": "Rapid response to security incidents."},
#                 {"title": "Security Consulting", "description": "Expert security consulting and advisory."}
#             ]
#         },
#         "testimonials": {
#             "title": "What Our Clients Say",
#             "items": []
#         }
#     }
#     return defaults.get(section, {})

# def generate_security_events():
#     import random
#     events = []
#     event_types = ['attack_blocked', 'intrusion_attempt', 'malware_detected', 'phishing_blocked', 'ddos_mitigated', 'vulnerability_scan']
#     severities = ['low', 'medium', 'high', 'critical']
#     statuses = ['detected', 'blocked', 'investigating', 'resolved']
#     countries = ['US', 'CN', 'RU', 'KP', 'IR', 'TR', 'BR', 'IN']
#     descriptions = [
#         'Suspicious login attempt detected',
#         'SQL injection attack blocked',
#         'Malware signature detected in upload',
#         'DDoS attack mitigated',
#         'Brute force attack on admin panel',
#         'Phishing attempt blocked',
#         'Vulnerability scan detected'
#     ]
    
#     for i in range(100):
#         random_days = random.randint(0, 30)
#         random_hours = random.randint(0, 23)
#         event_time = datetime.utcnow() - timedelta(days=random_days, hours=random_hours)
        
#         events.append({
#             "eventType": random.choice(event_types),
#             "severity": random.choice(severities),
#             "status": random.choice(statuses),
#             "description": random.choice(descriptions),
#             "source": {
#                 "ip": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
#                 "country": random.choice(countries)
#             },
#             "target": {
#                 "endpoint": f"/api/{random.choice(['login', 'dashboard', 'admin', 'upload', 'search'])}",
#                 "service": random.choice(['web', 'api', 'database', 'auth']),
#                 "port": random.choice([80, 443, 22, 3306])
#             },
#             "tags": ['automated'],
#             "createdAt": event_time,
#             "updatedAt": event_time
#         })
    
#     return events
