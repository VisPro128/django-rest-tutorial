from datetime import datetime
import io
from logging import disable
from django.http import response
from django.test import TestCase, Client
from django.test.utils import setup_test_environment
from django.urls import reverse as r
from django.contrib.auth.models import User
from snippets.models import Snippet
from snippets.serializers import SnippetSerializer
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from random import choice
import string

TEST_USER = "testuser"
TEST_PASS = "testpassword"

def setup_user():
    User.objects.create_superuser(
        username=TEST_USER,
        password=TEST_PASS,
        is_superuser=True,
        is_staff=True
    )

def disable_test(func):
    """Decorator that stops a test from being run"""
    pass

def create_snippet(code_text='',title_text=''):
    return Snippet.objects.create(code=code_text, 
                                  title=title_text, 
                                  owner=User.objects.first())

def print_current_objects():
    print('Current objects:')
    print(Snippet.objects.all())

def create_random_string(chars = string.ascii_letters + string.digits, N=10):
    return ''.join(choice(chars) for i in range(N))

def get_user_pk(username):
    try:
        user_pk = User.objects.all().filter(username=username).first().pk
    except AttributeError:
        user_pk = 0
    return user_pk

def login_user(client, username=TEST_USER, password=TEST_PASS):
    setup_user()
    response = client.login(username=username, password=password)
    return response


class SnippetCreationTests(TestCase):
    #@disable_test
    def test_snippet_created_date(self):
        """
        Test that a simple snippet has the correct date time added
        """
        client = Client()
        login_user(client)
        
        code_text = 'print("Hello, world")\n'
        snippet = create_snippet(code_text=code_text)
        
        #check that created time = current time
        self.assertEquals(
            f'{snippet.created.hour}:{snippet.created.minute}:{snippet.created.second}',
            f'{datetime.utcnow().hour}:{datetime.utcnow().minute}:{datetime.utcnow().second}',
            msg="Snippet auto-date does not match current UTC time")
        
        #check for correct auto-date
        self.assertEquals(
            snippet.created.date(), 
            datetime.utcnow().date(),
            msg="Snippet auto-date does not match current UTC date"
        )
        
        #check for 'UTC' timezone
        self.assertEquals(
            snippet.created.tzname(), 
            'UTC',
            msg="Snippet auto-date timezone is not 'UTC'"
        )
    
    #@disable_test
    def test_snippet_creation_no_code(self):
        """
        Test that evaluates the response of snippet creation without code text
        """
        client = Client()
        login_user(client)

        snippet = create_snippet()
        
        #check that snippet object exists and that code field is blank
        self.assertEquals(
            snippet.code, 
            '',
            msg="Snippet code text is not blank"
        )
    


class SnippetSerializerTests(TestCase):
    @disable_test
    def test_simple_create(self):
        """
        Test the creation of a simple snippet
        """
        client = Client()
        login_user(client)

        code_text = 'print("Hello, world")\n'
        snippet = create_snippet(code_text=code_text)
        serializer = SnippetSerializer(snippet)

        #check serialized code text vs original
        self.assertEquals(
            serializer.data['code'],
            code_text,
            msg="Serializer has not serialized code text correctly"
        )
        
        #check serialized title text vs original
        self.assertEquals(
            serializer.data['title'], 
            '',
            msg="Serializer has not serialized title text correctly"
        )
        
        #check serialized id number vs current last object
        self.assertEquals(
            serializer.data['id'], 
            Snippet.objects.last().id,
            msg="Serializer has not serialized id number correctly"
        )


class SnippetJSONRenderTests(TestCase):
    @disable_test
    def test_simple_JSON_render(self):
        """
        Test basic JSON conversion to and from
        """
        client = Client()
        login_user(client)

        code_text = 'print("Hello, world")\n'
        snippet = create_snippet(code_text=code_text)
        serializer1 = SnippetSerializer(snippet)
        content = JSONRenderer().render(serializer1.data)
        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serializer2 = SnippetSerializer(data=data)

        #check the data that has been converted to JSON and back is still valid
        self.assertTrue(
            serializer2.is_valid(), 
            msg="JSONParser data was not validated after serialization"
        )
        
        #check the validated JSON data is the right type
        self.assertEquals(
            str(type(serializer2.validated_data)), 
            "<class 'collections.OrderedDict'>",
            msg="JSONParser data was not serialized into an Ordered Dict"
        )
        
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

    @disable_test
    def test_JSON_render_with_blank_code(self):
        """
        Test basic JSON conversion to and from with no code text
        """
        client = Client()
        login_user(client)

        snippet = create_snippet(code_text='')
        serializer1 = SnippetSerializer(snippet)
        content = JSONRenderer().render(serializer1.data)
        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serializer2 = SnippetSerializer(data=data)

        #check the data that has been converted to JSON and back is invalid
        self.assertFalse(
            serializer2.is_valid(), 
            msg="JSONParser data was validated after serialization"
        )

        #check for the 'field may not be blank' error message
        self.assertEquals(
            str(serializer2.errors['code']), 
            "[ErrorDetail(string='This field may not be blank.', code='blank')]",
            msg="JSONParser did not return 'field may not be blank' error message"
        )
        
    @disable_test
    def test_JSON_render_with_long_title(self):
        """
        Test basic JSON conversion to and from with too long a title
        """
        client = Client()
        login_user(client)

        max_length = Snippet._meta.get_field('title').max_length
        title_text = create_random_string(N=max_length + 10)
        
        snippet = create_snippet(code_text='print(test)', title_text=title_text)
        serializer1 = SnippetSerializer(snippet)
        content = JSONRenderer().render(serializer1.data)
        stream = io.BytesIO(content)
        data = JSONParser().parse(stream)
        serializer2 = SnippetSerializer(data=data)

        #check the data that has been converted to JSON and back is still valid
        self.assertFalse(
            serializer2.is_valid(), 
            msg="JSONParser data with too long a title was validated after serialization"
        )

        #check for the 'too long' error message
        self.assertEquals(
            str(serializer2.errors['title']), 
            "[ErrorDetail(string='Ensure this field has no more than 100 characters.', code='max_length')]",
            msg="JSONParser did not return 'field too long' error message"
        )


class JSONAPITests(TestCase):
    #@disable_test
    def test_API_retrieval_simple(self):
        """
        Simple test to verify API retrieval for good input
        """
        client = Client()
        logged_in = login_user(client)

        #check that log in was successful
        self.assertTrue(logged_in, msg="Login was unsuccessful")
        response = client.post(r('snippet-list'), {'code': "This is a test"})

        response = client.get(r('snippet-detail', args=(response.data['id'],)))

        #check if response status code is 200 (OK)
        self.assertEquals(
            response.status_code,
            status.HTTP_200_OK,
            msg="Reponse code not 200 as expected"
        )

        #check if JSON response has returned a dictionary type
        self.assertEquals(
            str(type(response.json())),
            "<class 'dict'>",
            msg="JSON did not return dictionary type"
        )

        #check ID of snippet matches ID of returned JSON
        self.assertEquals(
            response.json()['id'],
            response.data['id'],
            msg="JSON returned mismatched ID"
        )

        #check snippet code matches code of returned JSON
        self.assertEquals(
            response.json()['code'],
            response.data['code'],
            msg="JSON returned mismatched code"
        )

    #@disable_test
    def test_API_retrieval_out_of_index(self):
        """
        Simple test to verify API retrieval for an index that doesn't exist
        """
        client = Client()
        logged_in = login_user(client)

        #check that log in was successful
        self.assertTrue(logged_in, msg="Login was unsuccessful")
        response = client.post(r('snippet-list'), {'code': "This is a test"})

        response = client.get(r('snippet-detail', args=(response.data['id'] + 1,)))

        #check if response status code is 404
        self.assertEquals(
            response.status_code, 
            status.HTTP_404_NOT_FOUND,
            msg="Reponse code not 404 as expected"
        )
    
    #@disable_test
    def test_authenticated_can_add(self):
        """
        Test to verify that an authenticated user can add
        """
        client = Client()
        logged_in = login_user(client)

        #check that log in was successful
        self.assertTrue(logged_in, msg="Login was unsuccessful")
        response = client.post(r('snippet-list'), {'code': "This is a test"})
        
        #check that response returns 201 created
        self.assertEquals(
            response.status_code, status.HTTP_201_CREATED,
            msg=f"Response was {response.status_code} instead of 201 created"
        )
        
    #@disable_test
    def test_authenticated_title_too_long(self):
        """
        Test to verify that an authenticated user cannot add a snippet with too long a title
        """
        client = Client()
        logged_in = login_user(client)

        #check that log in was successful
        self.assertTrue(logged_in, msg="Login was unsuccessful")

        title_text = create_random_string(N=110)
        response = client.post(
            r('snippet-list'),
            {
                'code': "This is a test",
                'title': title_text
            }
        )
        
        #check that 400 bad request has been returned
        self.assertEquals(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Response returned {response.status_code} instead of 400 bad request"
        )

        #check for the 'too long' error message
        self.assertEquals(
            repr(response.data['title']),
            "[ErrorDetail(string='Ensure this field has no more than 100 characters.', code='max_length')]",
            msg="Incorrect error message returned"
        )
        

    #@disable_test
    def test_non_authenticated_cannot_add(self):
        """
        Test to verify that a non-authenticated user cannot add
        """
        client = Client()
        response = client.post(r('snippet-list'), {'code': "This is a test"})
        
        #check that response returns 403 forbidden
        self.assertEquals(
            response.status_code, status.HTTP_403_FORBIDDEN,
            msg="Non-authenticated responses not 403 forbidden"
        )
    
    #@disable_test
    def test_highlight_hyperlink(self):
        """
        Test to verify that the hyperlink works on a created snippet
        """
        client = Client()
        login_user(client)
        response1 = client.post(r('snippet-list'), {'code': "This is a test"})

        response2 = client.get(r('snippet-detail', args=(response1.data['id'],)))
        highlight_url = response2.data['highlight']
        link = highlight_url[highlight_url.find("/snippets/"):]
        response3 = client.get(link)
        
        #check that response returned 200 OK
        self.assertEquals(
            response3.status_code,
            status.HTTP_200_OK,
            msg=f"Reponse returned {response3.status_code} instead of OK 200"
        )