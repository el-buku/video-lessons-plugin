import React from 'react';
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
	TextField
} from "@shopify/polaris";

import Axios from "axios";


class Admin extends React.Component {
	constructor(props) {
		super(props);
		this.state = {empty: true, rooms: [], new: false}
	}

	componentDidMount() {
		this.setState({loading: true}, () => {
			Axios.get('https://reqres.in/api/users?delay=3').then(
				result => {
					this.setState(
						{loading: false, rooms: result.data})
					if (this.state.rooms) this.setState({empty: false})
				})
		});
	}

	render() {

		const btn_action = {content: 'New Room', onAction: () => this.setState({new: true})}
		const empty = this.state.empty;
		const empty_component = <EmptyState
			heading="Schedule new video lesson rooms"
			action={btn_action}
			image="https://cdn.shopify.com/s/files/1/0757/9955/files/empty-state.svg"
		>
			<p>Schedule new video sessions</p>
		</EmptyState>
		const rooms = this.state.rooms;
		const video_el = <Page title="Video Rooms" separator primaryAction={btn_action}>
			<Layout>
				<Layout.AnnotatedSection title="Scheduled Rooms">
					{this.state.loading ? <Spinner size="large" color="teal"
					                               accessibilityLabel="spinner"/> : this.state.empty ? empty_component :
						<Rooms rooms={{rooms}}/>}


				</Layout.AnnotatedSection>
			</Layout>
		</Page>

		return (

			<div className="App">
				<AppProvider i18n={enTranslations}>
					{this.state.new ? <NewRoom/> : video_el}
				</AppProvider>
			</div>
		);
	}
}

class Rooms extends React.Component {
	constructor(props) {
		super(props);
	}

	render() {
		const rooms = this.props.rooms.rooms.data;
		// const items=[]
		// for (const room of this.props.rooms)
		// 	items.push(<Layout.oneThird><Room room={room}/> </Layout.oneThird>)
		return (
			<div>
				{rooms.map(room => <Layout.Section oneThird><Room room={{room}}/></Layout.Section>)}
			</div>
		)
	}
}

class Room extends React.Component {
	render() {
		const room = this.props.room.room
		return (
			<Card>{Object.keys(room).map(el => <div>{el}:{room[el]}</div>)}</Card>


		)
	}
}

class NewRoom extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			instructor: '',
			description: '',
			date: {month: 5, year: 2020},
			selectedDates: {start: new Date(), end: new Date()},
			hour: '0 EST',
			minutes: '0',
			duration: 0.5,
			price: '',
			imglink: ''
		}
	}

	render() {
		var options1 = () => {
			var arr = [];
			for (var h of Array(24).keys()) arr.push(h + ' EST');
			return arr;
		};
		var options2 = ['0', '15', '30', '45']
		const handleInstructorChange = (value) => this.setState({instructor: value});
		const handleDescriptionChange = (value) => this.setState({description: value});
		const handleMonthChange = (month, year) => this.setState({date: {month: month, year: year}});
		const handleDateChange = (date) => this.setState({selectedDates: date});
		const handleHourChange = (hour) => this.setState({hour: hour});
		const handleMinutesChange = (minutes) => this.setState({minutes: minutes})
		const handleRangeSliderChange = (duration) => this.setState({duration: duration})
		const handlePriceChange = (price) => this.setState({price: price})
		const handleImgChange = (link) => this.setState({imglink:link})
		const handleSubmit = ()=> {
			var state= this.state;
			console.log(state)
			Axios.post('http://insta-tag-checker.xyz/api/new_room', state).then(
				(response) => console.log(response),
				(error) => console.log(error)
			)
		}
		return (
			<Page title="Video Rooms" separator>
				<Layout>
					<Layout.AnnotatedSection title="Add new video room">
						<Card sectioned><Card.Section>

							<Form onSubmit={handleSubmit}>
								<FormLayout>
									<TextField label="Instructor" placeholder="This room's instructor's name"  minLength={1}
									           value={this.state.instructor} onChange={handleInstructorChange}/>
									<TextField label="Description" placeholder="Product's description"
									           value={this.state.description} onChange={handleDescriptionChange}/>
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
									<RangeSlider
										output
										label="Lession Duration (in hours)"
										min={0.5}
										max={4}
										step={0.5}
										value={this.state.duration}
										onChange={handleRangeSliderChange}
									/>
									<TextField label="Lesson Price (USD)" placeholder="Price for this lesson"
									           value={this.state.price} type="number" onChange={handlePriceChange}/>
									<TextField label="Product Image Link" placeholder="Link for the product's image"
									           value={this.state.imglink} type="url" onChange={handleImgChange}/>
						           <Button submit>Submit</Button>
								</FormLayout>
							</Form></Card.Section></Card>
					</Layout.AnnotatedSection>
				</Layout>
			</Page>
		)
	}
}

export default Admin;
