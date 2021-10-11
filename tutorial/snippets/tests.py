from datetime import datetime
import io
from django.test import TestCase
from snippets.models import Snippet
from snippets.serializers import SnippetSerializer
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser


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

def create_snippet(code_text):
    return Snippet.objects.create(code=code_text)


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
        self.assertEquals(snippet.created.date(), datetime.utcnow().date(),
                            msg="Snippet auto-date does not match current UTC date")
        
        #check for 'UTC' timezone
        self.assertEquals(snippet.created.tzname(), 'UTC',
                            msg="Snippet auto-date timezone is not 'UTC'")
        


class SnippetSerializerTests(TestCase):
    def test_simple_create(self):
        """
        Test the creation of a simple snippet
        """
        code_text = 'print("Hello, world")\n'
        snippet = create_snippet(code_text=code_text)
        serializer = SnippetSerializer(snippet)

        #check serialized code text vs original
        self.assertEquals(serializer.data['code'], code_text,
                            msg="Serializer has not serialized code text correctly")
        
        #check serialized title text vs original
        self.assertEquals(serializer.data['title'], '',
                            msg="Serializer has not serialized title text correctly")
        
        #check serialized id number vs current last object
        self.assertEquals(serializer.data['id'], Snippet.objects.last().id,
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