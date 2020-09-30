import React, {useCallback} from 'react';
import logo from './logo.svg';
import './App.css';
import '@shopify/polaris/styles.css'
import enTranslations from '@shopify/polaris/locales/en.json';

import {
	AppProvider,
	Button,
	Card, DatePicker,
	EmptyState,
	Form,
	FormLayout,
	Layout,
	Page, RangeSlider, Select,
	Spinner, Stack,
	TextField,
	ResourceList, ResourceItem,
	Badge
} from "@shopify/polaris";
import {Provider, TitleBar} from "@shopify/app-bridge-react"
import Axios from "axios";


class App extends React.Component {
	constructor(props) {
		super(props);
		var search = window.location.search
		var params = new URLSearchParams(search)
		var shop = params.get('shop')
		var apikey = params.get('apikey')
		this.state = {empty: true, instructors: [], new: false, email: false, shop: shop, apikey: apikey}
		this.handleNewRoom = this.handleNewRoom.bind(this)
		this.handleEmailSuccess = this.handleEmailSuccess.bind(this)
		this.handleDeleteInstructor = this.handleDeleteInstructor.bind(this)
		this.handleDeletePastRooms = this.handleDeletePastRooms.bind(this)
		this.getInstructors = this.getInstructors.bind(this)
		this.rerender = this.rerender.bind(this)
		this.btn_back = this.btn_back.bind(this)
	}


	componentDidMount() {
		this.getInstructors()
	}

	getInstructors() {
		this.setState({loading: true, empty: true}, () => {
			Axios.get('/api/get_instructors', {
				params: {
					shop: this.state.shop
				}
			}).then(
				result => {
					this.setState(
						{loading: false, instructors: result.data.response})
					if (this.state.instructors.length > 0) this.setState({empty: false})
				})
		});
	}

	rerender() {
		this.setState({new: false, instructor_id: null})
		this.getInstructors()
	}

	handleNewRoom(instructor_id) {
		this.setState({new: true, instructor_id: instructor_id})
	}

	handleDeleteInstructor(instructor_id) {
		Axios.get('/api/delete_instructor/' + instructor_id.toString() + '?shop=' + this.state.shop).then(
			response => this.getInstructors(), error => console.log(error)
		)
	}

	handleDeletePastRooms(instructor_id) {
		Axios.get('/api/delete_past_rooms/' + instructor_id.toString()).then(
			response => this.getInstructors(),
			error => console.log(error)
		)
	}

	handleEmailSuccess() {
		this.setState({new: false, email: false})
	}

	btn_back() {
		this.setState({new: false, email: false, instructor_id: false})
		this.getInstructors()
	}


	render() {
		const btn_action = {
			content: 'Edit e-mail notification',
			onAction: () => this.setState({new: true, email: true})
		}
		const back_btn = {content: 'Go back', onAction: this.btn_back}
		const empty = this.state.empty;
		const empty_component = <EmptyState
			heading="Schedule new video lesson rooms"
			image="https://cdn.shopify.com/s/files/1/0757/9955/files/empty-state.svg"
		>
			<p>Add instructors in your admin and come back here to schedule video lessons.</p>
		</EmptyState>
		const instructors = this.state.instructors;
		const video_el = <Page>
			<TitleBar title='Video Lessons' separator primaryAction={btn_action}/>
			<Layout>
				{/*<Layout.AnnotatedSection title="Scheduled Rooms">*/}
				{this.state.loading ? <Spinner size="large" color="teal"
				                               accessibilityLabel="spinner"/> : this.state.empty ? empty_component :
					<Instructors instructors={{instructors}} handle={this.handleNewRoom}
					             deleteInstructor={this.handleDeleteInstructor}
					             deletePastRooms={this.handleDeletePastRooms}
					             rerender={this.rerender}/>}


				{/*</Layout.AnnotatedSection>*/}
			</Layout>
		</Page>
		const el = () => {
			if (this.state.email) return <EditEmail shop={this.state.shop} handle={this.handleEmailSuccess}
			                                        back={this.btn_back}/>
			else return <NewRoom rerender={this.rerender} shop={this.state.shop}
			                     instructor_id={this.state.instructor_id}/>
		}
		const new_el = <Page>
			<TitleBar title='Video Lessons' separator primaryAction={back_btn}/>
			{el()}
			<Layout>
			</Layout>
		</Page>
		const config = {
			apiKey: this.state.apikey,
			shopOrigin: this.state.shop,
			forceRedirect: true
		}
		return (

			<div className="App">
				<AppProvider i18n={enTranslations}>
					<Provider config={config}>
						{this.state.new ? new_el : video_el}
					</Provider>
				</AppProvider>
			</div>
		);
	}
}

class Instructors extends React.Component {
	constructor(props) {
		super(props);
	}

	render() {
		const instructors = this.props.instructors.instructors;
		const list = instructors.map(
			instructor =>
				<Instructor instructor={instructor} key={instructor.id} handle={this.props.handle}
				            rerender={this.props.rerender} deleteInstructor={this.props.deleteInstructor}
				            deletePastRooms={this.props.deletePastRooms}/>
		)

		var i = 0;
		var arr1 = []
		var arr2 = []
		var arr3 = []
		for (var instructor of list) {
			if (i % 3 == 0) arr1.push(instructor);
			if (i % 3 == 1) arr2.push(instructor);
			if (i % 3 == 2) arr3.push(instructor);
			i = i + 1;
		}
		// const items=[]
		// for (const room of this.props.rooms)
		// 	items.push(<Layout.oneThird><Room room={room}/> </Layout.oneThird>)
		return (
			<>
				<Layout.Section oneThird>{arr1}</Layout.Section>
				<Layout.Section oneThird>{arr2}</Layout.Section>

				<Layout.Section oneThird>{arr3}</Layout.Section>
			</>
		)
	}
}

class Instructor extends React.Component {
	constructor(props) {
		super(props);
		this.handleDelete = this.handleDelete.bind(this)
	}

	handleDelete(id) {
		Axios.get('/api/delete_room/' + id.toString()).then(
			respose => this.props.rerender(), error => console.log(error)
		)
	}

	render() {
		const instructor = this.props.instructor
		return (

			<Card title={instructor.title} sectioned secondaryFooterActions={[{
				content: 'Delete',
				onAction: () => this.props.deleteInstructor(instructor.id),
				destructive: true
			}, {
				content: 'Delete past rooms',
				onAction: () => this.props.deletePastRooms(instructor.id)
			}]}
			      primaryFooterAction={{content: 'New Room', onAction: () => this.props.handle(instructor.id)}}>

				<Card.Section>
					{instructor.body_html}
				</Card.Section>
				<Card.Section title='Upcoming rooms'>
					<ResourceList resourceName={{singular: 'room', plural: 'rooms'}}
					              items={instructor.upcoming_rooms} renderItem={
						(room) => {
							const {admin_pass, link, variant_title, room_name, count, room_id} = room;
							return (
								<ResourceItem verticalAlignment='center' id={room_name}>
									<Stack>
										<div>{variant_title}</div>
										<div>Pass: {admin_pass}</div>
										<div>Room Name: {room_name}</div>
										<div>Attendees: {count}/3</div>
										<div><span><a href={link}>Link</a> <a href=''
										                                      onClick={() => this.handleDelete(room_id)}>Delete</a> </span>
										</div>

									</Stack>
								</ResourceItem>
							)
						}
					}/>
				</Card.Section>
				<Card.Section title='Past Rooms' subdued>
					<ResourceList resourceName={{singular: 'room', plural: 'rooms'}}
					              items={instructor.past_rooms} renderItem={
						(room) => {
							const {admin_pass, link, variant_title, room_name, count, room_id} = room;
							return (
								<ResourceItem verticalAlignment='center' id={room_name}>
									<Stack>
										<div>{variant_title}</div>
										<div>Pass: {admin_pass}</div>
										<div>Room Name: {room_name}</div>
										<div>Attendees: {count}/3</div>
										<div><a href={link}>{link}</a></div>
										<div><Button destructive plain
										             onClick={() => this.handleDelete(room_id)}>Delete</Button>
										</div>

									</Stack>
								</ResourceItem>
							)
						}
					}/>
				</Card.Section>
			</Card>
			// <Card>{Object.keys(room).map(el => <div>{el}:{room[el]}</div>)}</Card>


		)
	}
}

class NewRoom extends React.Component {
	constructor(props) {
		super(props);
		const shop = this.props.shop
		const instructor_id = this.props.instructor_id
		let date = new Date()
		date.setHours(0)
		date.setMinutes(0)
		date.setSeconds(0)
		this.state = {
			instructor: instructor_id,
			description: '',
			date: {month: date.getMonth(), year: date.getFullYear()},
			selectedDates: {start: date, end: date},
			hour: '0 EST',
			minutes: '0',
			duration: 0.5,
			price: '',
			imglink: '',
			shop: shop
		}
	}

	render() {
		var options1 = () => {
			var arr = [];
			for (var h of Array(24).keys()) arr.push(h + ' EST');
			return arr;
		};
		var options2 = ['0', '15', '30', '45']
		// const handleInstructorChange = (value) => this.setState({instructor: value});
		// const handleDescriptionChange = (value) => this.setState({description: value});
		const handleMonthChange = (month, year) => this.setState({date: {month: month, year: year}});
		const handleDateChange = (date) => this.setState({selectedDates: date});
		const handleHourChange = (hour) => this.setState({hour: hour});
		const handleMinutesChange = (minutes) => this.setState({minutes: minutes})
		// const handleRangeSliderChange = (duration) => this.setState({duration: duration})
		const handlePriceChange = (price) => this.setState({price: price})
		// const handleImgChange = (link) => this.setState({imglink: link})
		const handleSubmit = () => {

			var state = this.state;
			console.log(state)
			if (state.price) {
				Axios.post('/api/new_room', state).then(
					(response) => {
						if (!response.data.error) {
							console.log(response);
							this.props.rerender()
						} else alert('Room already exists')
					},
					(error) => alert('Error. Probably the room exists or the date has passed already.')
				)
			} else alert("Don't leave empty fields.")

		}
		return (

			<Card sectioned><Card.Section>

				<Form onSubmit={handleSubmit}>
					<FormLayout>
						{/*<TextField label="Instructor" placeholder="This room's instructor's name"*/}
						{/*           minLength={1}*/}
						{/*           value={this.state.instructor} onChange={handleInstructorChange}/>*/}
						{/*<TextField label="Description" placeholder="Product's description"*/}
						{/*           value={this.state.description} onChange={handleDescriptionChange}/>*/}
						<DatePicker month={this.state.date.month} year={this.state.date.year}
						            onMonthChange={handleMonthChange} selected={this.state.selectedDates}
						            onChange={handleDateChange}/>
						<Stack vertical spacing="extraTight">
							<FormLayout.Group condensed>
								<Select label="Start Hour" options={options1()} value={this.state.hour}
								        onChange={handleHourChange}/>
								<Select label="Start Minutes" options={options2} value={this.state.minutes}
								        onChange={handleMinutesChange}/>

							</FormLayout.Group>
						</Stack>
						<TextField label="Lesson Price (USD)" placeholder="Price for this lesson"
						           value={this.state.price} type="number" onChange={handlePriceChange}/>
						{/*<TextField label="Product Image Link" placeholder="Link for the product's image"*/}
						{/*           value={this.state.imglink} type="url" onChange={handleImgChange}/>*/}
						<Button submit>Submit</Button>
					</FormLayout>
				</Form></Card.Section></Card>

		)
	}
}

class EditEmail extends React.Component {
	constructor(props) {
		super(props);
		this.state = {loading: true, title: null, msg: null, html:null}
	}

	componentDidMount() {
		Axios.get('/api/get_message', {
			params: {
				shop: this.props.shop
			}
		}).then(result => this.setState({
			loading: false,
			title: result.data.message.title,
			msg: result.data.message.body,
			html: result.data.message.html,
		}), error => console.log(error))
	}

	render() {
		const state = this.state
		const handleTitleChange = (title) => this.setState({title: title})
		const handleMsgChange = (msg) => this.setState({msg: msg})
		const handleHtmlChange = (html) => this.setState({html:html})
		const handleSubmit = () => {
			if (this.state.title && this.state.msg) {
				Axios.get('/api/edit_message?shop=' + this.props.shop, {
					params: state
				}).then(result => this.props.handle(), error => console.log(error))
			} else alert("Don't leave empty fields.")
		}
		return (

			<Card sectioned><Card.Section>

				<Form onSubmit={handleSubmit}>
					<FormLayout>
						<TextField label="E-mail title" placeholder="E-mail plain text template"
						           minLength={1} value={this.state.title} onChange={handleTitleChange}/>
						<TextField label="E-mail body" placeholder="E-mail body"
						           multiline minLength={1} value={this.state.msg} onChange={handleMsgChange}/>
						<TextField label="E-mail HTML" placeholder="E-mail HTML template"
						           multiline minLength={1} value={this.state.html} onChange={handleHtmlChange}/>
						<Button submit>Submit</Button>
					</FormLayout>
				</Form></Card.Section></Card>
		)
	}
}

export default App;
