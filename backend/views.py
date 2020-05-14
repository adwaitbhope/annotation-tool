from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from backend.models import Image, Project, Category
import json
from PIL import Image as Img
import os
import random
import xml.dom.minidom
import xml.etree.cElementTree as ET


def generate_xml(payload, xml_path):
    boxes, labels, image = payload['boxes'], payload['labels'], payload['image'],

    image_name = os.path.split(image['path'])[1]
    image_dir = os.path.split(os.path.split(image['path'])[0])[1]
    file_name = os.path.join(xml_path, os.path.splitext(image_name)[0])     # file name of generated xml

    width, height, depth = image['width'], image['height'], image['depth']

    annotation = ET.Element('annotation')
    ET.SubElement(annotation, 'folder').text = image_dir
    ET.SubElement(annotation, 'filename').text = os.path.split(image_name)[1]
    ET.SubElement(annotation, 'path').text = image['path']

    source = ET.SubElement(annotation, 'source')
    ET.SubElement(source, 'database').text = 'Unknown'

    size = ET.SubElement(annotation, 'size')
    ET.SubElement(size, 'width').text = str(width)
    ET.SubElement(size, 'height').text = str(height)
    ET.SubElement(size, 'depth').text = str(depth)

    ET.SubElement(annotation, 'segmented').text = '0'

    for box, label in zip(boxes, labels):
        object = ET.SubElement(annotation, 'object')
        ET.SubElement(object, 'name').text = label
        ET.SubElement(object, 'pose').text = 'Unspecified'
        ET.SubElement(object, 'truncated').text = '0'
        ET.SubElement(object, 'difficult').text = '0'

        bndbox = ET.SubElement(object, 'bndbox')
        ET.SubElement(bndbox, 'xmin').text = str(box['xmin'])
        ET.SubElement(bndbox, 'ymin').text = str(box['ymin'])
        ET.SubElement(bndbox, 'xmax').text = str(box['xmax'])
        ET.SubElement(bndbox, 'ymax').text = str(box['ymax'])

    tree = ET.ElementTree(annotation)
    tree.write(file_name + '.xml')

    dom = xml.dom.minidom.parse(file_name + '.xml')
    pretty_xml_as_string = dom.toprettyxml()

    file = open(file_name + '.xml', 'w')
    file.write(pretty_xml_as_string)
    file.close()


def index(request):
    return HttpResponse("Hello, world. You're at the index.")


def get_next_image(project):
    # TODO: optimize following query (merge into one)
    project = Project.objects.get(name=project)
    images = Image.objects.filter(project=project, annotated=False)

    if len(images) == 0:
        # TODO: render a standard page with error description
        raise Exception("No images left for annotation.")

    image = random.choice(images)
    return image.name


def mark_annotated(project, image_name):
    # TODO: optimize following query (merge into one)
    project = Project.objects.get(name=project)
    image = Image.objects.get(project=project, name=image_name)
    image.annotated = True
    image.save()


def get_categories(project):
    categories = Category.objects.filter(project=project)

    if len(categories) == 0:
        # TODO: render a standard page with error description
        raise Exception("No categories set for this project.")

    categories = json.dumps([category.name for category in categories])
    return categories


@csrf_exempt
def submit_annotations(request, project):
    payload = json.loads(request.body)
    image_name = os.path.split(payload['image']['path'])[1]

    project_dir = os.path.join(settings.MEDIA_URL, project)
    project_dir_abs = os.path.join(settings.MEDIA_ROOT, project)

    generate_xml(payload, os.path.join(project_dir_abs, 'annotations'))
    mark_annotated(project, image_name)

    image_name = os.path.join('images', get_next_image(project))
    image_path = os.path.abspath(os.path.join(project_dir_abs, image_name))
    image = Img.open(image_path)

    context = {
        'image_src': os.path.join(project_dir, image_name),
        'image_width': image.size[0],
        'image_height': image.size[1],
        'image_depth': 3
    }

    return JsonResponse(context, safe=False)


def annotate(request, project):
    project_entry = Project.objects.get(name=project)
    if project_entry is None:
        raise Http404('This project does not exist.')

    project_dir = os.path.join(settings.MEDIA_URL, project)
    project_dir_abs = os.path.join(settings.MEDIA_ROOT, project)

    image_name = os.path.join('images', get_next_image(project))
    image_path = os.path.abspath(os.path.join(project_dir_abs, image_name))
    image = Img.open(image_path)

    categories = get_categories(project_entry)

    context = {
        'project': project,
        'project_title': project.upper(),
        'submit_url': settings.HOSTED_URL + 'submit/' + project,
        'image_src': os.path.join(project_dir, image_name),
        'image_width': image.size[0],
        'image_height': image.size[1],
        'image_depth': 3,
        'categories': categories
    }

    return render(request, 'image_view.html', context=context)
