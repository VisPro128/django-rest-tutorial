from datetime import datetime
import io
from django.test import TestCase, Client
from django.test.utils import setup_test_environment
from django.urls import reverse
from snippets.models import Snippet
from snippets.serializers import SnippetSerializer
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from random import choice
import string

"""
Example test case
class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        "
        If no questions exist, an appropriate message is displayed.
        "
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])
"""

def create_snippet(code_text='',title_text=''):
    return Snippet.objects.create(code=code_text, title=title_text)

def print_current_objects():
    print('Current objects:')
    print(Snippet.objects.all())

def create_random_string(chars = string.ascii_letters + string.digits, N=10):
    return ''.join(choice(chars) for i in range(N))

class SnippetCreationTests(TestCase):
    def test_snippet_created_date(self):
        """
        Test that a simple snippet has the correct date time added
        """
        code_text = 'print("Hello, world")\n'
        snippet = create_snippet(code_text=code_text)
        
        #check that created time = current time
        self.assertEquals(
            f'{snippet.created.hour}:{snippet.created.minute}:{snippet.created.second}',
            f'{datetime.utcnow().hour}:{datetime.utcnow().minute}:{datetime.utcnow().second}',
            msg="Snippet auto-date does not match current UTC time")
        
        #check for correct auto-date
        self.assertEquals(snippet.created.date(), 
                          datetime.utcnow().date(),
                          msg="Snippet auto-date does not match current UTC date")
        
        #check for 'UTC' timezone
        self.assertEquals(snippet.created.tzname(), 
                          'UTC',
                          msg="Snippet auto-date timezone is not 'UTC'")
    
    def test_snippet_creation_no_code(self):
        """
        Test that evaluates the response of snippet creation without code text
        """
        snippet = create_snippet()
        
        #check that snippet object exists and that code field is blank
        self.assertEquals(snippet.code, 
                          '',
                          msg="Snippet code text is not blank")
    
    #def test_long_title(self):
        #"""
        #Test the response of a title exceeding the character limit
        #"""
        #max_length = Snippet._meta.get_field('title').max_length

        #title_text = create_random_string(N=max_length + 10)
        
        #snippet = create_snippet(title_text=title_text)
        #print(len(snippet.title))
        #####################################################


class SnippetSerializerTests(TestCase):
    def test_simple_create(self):
        """
        Test the creation of a simple snippet
        """
        code_text = 'print("Hello, world")\n'
        snippet = create_snippet(code_text=code_text)
        serializer = SnippetSerializer(snippet)

        #check serialized code text vs original
        self.assertEquals(serializer.data['code'],
                          code_text,
                          msg="Serializer has not serialized code text correctly")
        
        #check serialized title text vs original
        self.assertEquals(serializer.data['title'], 
                          '',
                          msg="Serializer has not serialized title text correctly")
        
        #check serialized id number vs current last object
        self.assertEquals(serializer.data['id'], 
                          Snippet.objects.last().id,
                          msg="Serializer has not serialized id number correctly")


class SnippetJSONRenderTests(TestCase):
    def test_simple_JSON_render(self):
        """
        Test basic JSON conversion to and from
        """
        code_text = 'print("Hello, world")\n'
        snippet = create_snippet(code_text=code_text)
        serializer1 = SnippetSerializer(snippet)
        content = JSONRenderer().render(serializer1.data)
        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serializer2 = SnippetSerializer(data=data)

        #check the data that has been converted to JSON and back is still valid
        self.assertTrue(serializer2.is_valid(), 
                        msg="JSONParser data was not validated after serialization")
        
        #check the validated JSON data is the right type
        self.assertEquals(str(type(serializer2.validated_data)), 
                          "<class 'collections.OrderedDict'>",
                          msg="JSONParser data was not serialized into an Ordered Dict")
        
        #check that the code text has not changed through the sending and validation process
        #self.assertEquals(serializer2.validated_data['code'], code_text, 
        #                    msg="Validated code data string does not match original")
        
        #check that the dictionaries from before and after JSON conversion match
        #print("Data before JSON conversion")
        #print(serializer1.data)
        #print("Data after JSON conversion")
        #print(serializer2.validated_data)
        #self.assertDictEqual(serializer1.data, serializer2.validated_data,
        #                    msg="Validated serialized dictionary does not match original")

    def test_JSON_render_with_blank_code(self):
        """
        Test basic JSON conversion to and from with no code text
        """
        snippet = create_snippet(code_text='')
        serializer1 = SnippetSerializer(snippet)
        content = JSONRenderer().render(serializer1.data)
        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serializer2 = SnippetSerializer(data=data)

        #check the data that has been converted to JSON and back is invalid
        self.assertFalse(serializer2.is_valid(), 
                         msg="JSONParser data was validated after serialization")

        #check for the 'field may not be blank' error message
        self.assertEquals(str(serializer2.errors['code']), 
            "[ErrorDetail(string='This field may not be blank.', code='blank')]",
            msg="JSONParser did not return 'field may not be blank' error message")
        
    
    def test_JSON_render_with_long_title(self):
        """
        Test basic JSON conversion to and from with too long a title
        """
        max_length = Snippet._meta.get_field('title').max_length
        title_text = create_random_string(N=max_length + 10)
        
        snippet = create_snippet(code_text='print(test)', title_text=title_text)
        serializer1 = SnippetSerializer(snippet)
        content = JSONRenderer().render(serializer1.data)
        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serializer2 = SnippetSerializer(data=data)

        #check the data that has been converted to JSON and back is still valid
        self.assertFalse(serializer2.is_valid(), 
                         msg="JSONParser data with too long a title " + \
                             "was validated after serialization")

        #check for the 'too long' error message
        self.assertEquals(str(serializer2.errors['title']), 
            "[ErrorDetail(string='Ensure this field has no more than 100 characters.', code='max_length')]",
            msg="JSONParser did not return 'field too long' error message")


class JSONAPITests(TestCase):
    def test_API_retrieval_simple(self):
        """
        Simple test to verify API retrieval for good input
        """
        client = Client()
        snippet = create_snippet("print('this is test test test)")
        response = client.get(reverse('snippets-detail-view', args=(snippet.id,)))

        #check if response status code is 200 (OK)
        self.assertEquals(response.status_code,
                          status.HTTP_200_OK,
                          msg="Reponse code not 200 as expected")

        #check if JSON response has returned a dictionary type
        self.assertEquals(str(type(response.json())),
                          "<class 'dict'>",
                          msg="JSON did not return dictionary type")

        #check ID of snippet matches ID of returned JSON
        self.assertEquals(response.json()['id'],
                          snippet.id,
                          msg="JSON returned mismatched ID")

        #check snippet code matches code of returned JSON
        self.assertEquals(response.json()['code'],
                          snippet.code,
                          msg="JSON returned mismatched code")
    
    def test_API_retrieval_out_of_index(self):
        """
        Simple test to verify API retrieval for an index that doesn't exist
        """
        client = Client()
        snippet = create_snippet("print('this is test test test)")
        response = client.get(reverse('snippets-detail-view', args=(snippet.id + 1,)))

        #check if response status code is 404
        self.assertEquals(response.status_code, 
                          status.HTTP_404_NOT_FOUND,
                          msg="Reponse code not 404 as expected")