import os
from datetime import datetime
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import gpxpy
import gpxpy.gpx
from fpdf import FPDF
import json


class PDFExporter:
    def __init__(self, personal_route):
        self.route = personal_route

    def export_to_pdf(self, filename=None):
        if not filename:
            filename = f"маршрут_{self.route.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

        filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()

        # Стили
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#2C3E50')
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#34495E')
        )

        # Содержимое документа
        story = []

        # Заголовок
        story.append(Paragraph(f"Маршрут: {self.route.name}", title_style))
        story.append(Spacer(1, 0.5 * cm))

        # Информация о маршруте
        if self.route.description:
            story.append(Paragraph("Описание:", heading_style))
            story.append(Paragraph(self.route.description, styles['Normal']))
            story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph(f"Создан: {self.route.created_at.strftime('%d.%m.%Y')}", styles['Normal']))
        story.append(Paragraph(f"Количество точек: {self.route.get_points_count()}", styles['Normal']))
        story.append(Paragraph(f"Общая длительность: {self.route.get_total_duration()} ч", styles['Normal']))
        story.append(Spacer(1, 1 * cm))

        # Таблица точек маршрута
        story.append(Paragraph("Точки маршрута:", heading_style))

        table_data = [['№', 'Название', 'Тип', 'Время (мин)', 'Описание']]

        for point in self.route.points.all().order_by('order'):
            table_data.append([
                str(point.order),
                point.waypoint.name,
                point.waypoint.get_waypoint_type_display(),
                str(point.planned_visit_time),
                point.waypoint.short_description[:100] + '...' if point.waypoint.short_description and len(
                    point.waypoint.short_description) > 100 else point.waypoint.short_description or ''
            ])

        table = Table(table_data, colWidths=[1 * cm, 4 * cm, 3 * cm, 2 * cm, 6 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1ABC9C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
        story.append(Spacer(1, 1 * cm))

        # Детали по точкам
        story.append(Paragraph("Подробная информация о точках:", heading_style))

        for point in self.route.points.all().order_by('order'):
            story.append(
                Paragraph(f"{point.order}. {point.waypoint.name} ({point.waypoint.get_waypoint_type_display()})",
                          styles['Heading3']))

            if point.waypoint.short_description:
                story.append(Paragraph(point.waypoint.short_description, styles['Normal']))

            if point.notes:
                story.append(Paragraph(f"<b>Мои заметки:</b> {point.notes}", styles['Normal']))

            story.append(Paragraph(f"<b>Координаты:</b> {point.waypoint.latitude}, {point.waypoint.longitude}",
                                   styles['Normal']))
            story.append(Spacer(1, 0.2 * cm))

        doc.build(story)
        return filepath


class GPXExporter:
    def __init__(self, personal_route):
        self.route = personal_route

    def export_to_gpx(self, filename=None):
        if not filename:
            filename = f"маршрут_{self.route.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.gpx"

        filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        gpx = gpxpy.gpx.GPX()

        # Метаданные маршрута
        gpx.name = self.route.name
        gpx.description = self.route.description
        gpx.author_name = self.route.user.get_full_name() or self.route.user.username
        gpx.time = datetime.now()

        # Создаем маршрут
        gpx_route = gpxpy.gpx.GPXRoute()
        gpx_route.name = self.route.name
        gpx_route.description = self.route.description

        # Добавляем точки в маршрут
        for point in self.route.points.all().order_by('order'):
            gpx_point = gpxpy.gpx.GPXRoutePoint(
                latitude=point.waypoint.latitude,
                longitude=point.waypoint.longitude,
                elevation=point.waypoint.altitude or 0
            )
            gpx_point.name = f"{point.order}. {point.waypoint.name}"
            gpx_point.description = point.waypoint.short_description
            gpx_point.type = point.waypoint.get_waypoint_type_display()

            gpx_route.points.append(gpx_point)

        gpx.routes.append(gpx_route)

        # Также добавляем точки как waypoints для навигации
        for point in self.route.points.all().order_by('order'):
            gpx_waypoint = gpxpy.gpx.GPXWaypoint(
                latitude=point.waypoint.latitude,
                longitude=point.waypoint.longitude,
                elevation=point.waypoint.altitude or 0
            )
            gpx_waypoint.name = f"{point.order}. {point.waypoint.name}"
            gpx_waypoint.description = point.waypoint.short_description
            gpx_waypoint.type = point.waypoint.get_waypoint_type_display()

            gpx.waypoints.append(gpx_waypoint)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(gpx.to_xml())

        return filepath


class SimplePDFExporter(FPDF):
    def __init__(self, personal_route):
        super().__init__()
        self.route = personal_route

    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, f'Маршрут: {self.route.name}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Страница {self.page_no()}', 0, 0, 'C')

    def export_simple_pdf(self, filename=None):
        if not filename:
            filename = f"маршрут_{self.route.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

        filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.add_page()
        self.set_font('Arial', '', 12)

        # Информация о маршруте
        self.cell(0, 10, f'Описание: {self.route.description}', 0, 1)
        self.cell(0, 10, f'Создан: {self.route.created_at.strftime("%d.%m.%Y")}', 0, 1)
        self.cell(0, 10, f'Точек: {self.route.get_points_count()}', 0, 1)
        self.cell(0, 10, f'Длительность: {self.route.get_total_duration()} ч', 0, 1)

        self.ln(10)

        # Точки маршрута
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Точки маршрута:', 0, 1)
        self.ln(5)

        for point in self.route.points.all().order_by('order'):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, f'{point.order}. {point.waypoint.name} ({point.waypoint.get_waypoint_type_display()})', 0,
                      1)

            self.set_font('Arial', '', 10)
            if point.waypoint.short_description:
                self.multi_cell(0, 8, point.waypoint.short_description)

            self.cell(0, 8, f'Координаты: {point.waypoint.latitude}, {point.waypoint.longitude}', 0, 1)
            self.cell(0, 8, f'Время посещения: {point.planned_visit_time} мин', 0, 1)

            if point.notes:
                self.set_font('Arial', 'I', 10)
                self.multi_cell(0, 8, f'Заметки: {point.notes}')

            self.ln(5)

        self.output(filepath)
        return filepath
